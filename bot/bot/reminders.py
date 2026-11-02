import asyncio
import datetime as dt
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from bot import texts
from bot.db.models import Subscription
from bot.db.repo import get_latest_subscriptions_around
from bot.db.session import get_session
from bot.keyboards import renew_menu

logger = logging.getLogger(__name__)

CHECK_INTERVAL = dt.timedelta(minutes=30)
REMIND_3D = dt.timedelta(days=3)
REMIND_1D = dt.timedelta(days=1)
# Об окончании сообщаем только по свежим подпискам — чтобы после деплоя не
# разослать «подписка закончилась» всем, у кого она кончилась месяц назад.
EXPIRED_NOTICE_WINDOW = dt.timedelta(days=2)


async def reminder_loop(bot: Bot) -> None:
    while True:
        try:
            await _send_due_reminders(bot)
        except Exception:
            logger.exception("Reminder loop iteration failed")
        await asyncio.sleep(CHECK_INTERVAL.total_seconds())


def _due_reminder(subscription: Subscription, now: dt.datetime) -> tuple[str, str] | None:
    """Какое напоминание пора отправить: (имя флага, текст) или None."""
    left = subscription.expires_at - now
    expires = subscription.expires_at.strftime("%d.%m.%Y")

    if left <= dt.timedelta(0):
        if not subscription.expired_notified:
            return "expired_notified", texts.SUBSCRIPTION_EXPIRED
        return None
    if left <= REMIND_1D:
        if not subscription.reminder_sent:
            return "reminder_sent", texts.REMINDER_1D.format(expires=expires)
        return None
    # за 3 дня — только если подписка изначально была длиннее 3 дней,
    # иначе напоминание придёт сразу после покупки
    if left <= REMIND_3D and subscription.expires_at - subscription.created_at > REMIND_3D:
        if not subscription.reminder_3d_sent:
            return "reminder_3d_sent", texts.REMINDER_3D.format(expires=expires, left=texts.time_left_label(left))
    return None


async def _send_due_reminders(bot: Bot) -> None:
    now = dt.datetime.utcnow()
    async with get_session() as session:
        candidates = await get_latest_subscriptions_around(
            session, before=REMIND_3D, after=EXPIRED_NOTICE_WINDOW
        )

        changed = False
        for subscription, user in candidates:
            due = _due_reminder(subscription, now)
            if due is None:
                continue
            flag, text = due

            try:
                await bot.send_message(user.tg_id, text, reply_markup=renew_menu())
            except (TelegramForbiddenError, TelegramBadRequest):
                logger.info("Can't message tg_id=%s (blocked or never started), skipping reminder", user.tg_id)
            except Exception:
                logger.exception("Failed to send reminder to tg_id=%s", user.tg_id)
                continue

            # Отмечаем и предыдущие этапы — после отправки «завтра» уже не
            # нужно присылать «через 3 дня».
            subscription.reminder_3d_sent = True
            if flag in ("reminder_sent", "expired_notified"):
                subscription.reminder_sent = True
            if flag == "expired_notified":
                subscription.expired_notified = True
            changed = True

        if changed:
            await session.commit()

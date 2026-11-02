import asyncio
import datetime as dt
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from bot import texts
from bot.db.repo import get_subscriptions_expiring_soon
from bot.db.session import get_session

logger = logging.getLogger(__name__)

CHECK_INTERVAL = dt.timedelta(hours=1)
REMIND_WITHIN = dt.timedelta(hours=24)


async def reminder_loop(bot: Bot) -> None:
    while True:
        try:
            await _send_due_reminders(bot)
        except Exception:
            logger.exception("Reminder loop iteration failed")
        await asyncio.sleep(CHECK_INTERVAL.total_seconds())


async def _send_due_reminders(bot: Bot) -> None:
    async with get_session() as session:
        due = await get_subscriptions_expiring_soon(session, within=REMIND_WITHIN)

        for subscription, user in due:
            try:
                await bot.send_message(
                    user.tg_id,
                    texts.REMINDER.format(expires=subscription.expires_at.strftime("%d.%m.%Y")),
                )
            except TelegramForbiddenError:
                logger.info("User %s blocked the bot, skipping reminder", user.tg_id)
            except Exception:
                logger.exception("Failed to send reminder to tg_id=%s", user.tg_id)
                continue

            subscription.reminder_sent = True

        if due:
            await session.commit()

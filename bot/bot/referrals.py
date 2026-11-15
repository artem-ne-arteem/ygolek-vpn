"""Реферальная программа.

Ссылка t.me/<бот>?start=ref_<tg_id>. Новый человек, пришедший по ней,
привязывается к пригласившему. Когда он впервые оплачивает подписку (звёздами
или картой), пригласившему засчитывается +1 друг. За каждые
REFERRALS_FOR_REWARD засчитанных друзей — REFERRAL_REWARD_DAYS дней бесплатно.
"""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot import texts
from bot.db.models import Payment, Subscription, User
from bot.db.repo import marzban_username_for, record_subscription
from bot.db.session import get_session
from bot.devices import carry_extra_devices, device_limit_for
from bot.h1panel.client import H1PanelClient, H1PanelError
from bot.keyboards import back_to_menu
from bot.plans import REFERRAL_REWARD_DAYS, REFERRALS_FOR_REWARD

logger = logging.getLogger(__name__)

START_PREFIX = "ref_"


def referral_link(bot_username: str, tg_id: int) -> str:
    return f"https://t.me/{bot_username}?start={START_PREFIX}{tg_id}"


async def attach_referrer(session: AsyncSession, user: User, start_args: str | None) -> None:
    """Привязывает пригласившего по /start ref_<tg_id>.

    Только для новых клиентов — у кого ещё не было ни подписок, ни оплат, —
    чтобы нельзя было «переписать» себя на друга задним числом.
    """
    if not start_args or not start_args.startswith(START_PREFIX) or user.referred_by is not None:
        return
    ref_tg_id = start_args.removeprefix(START_PREFIX)
    if not ref_tg_id.isdigit() or int(ref_tg_id) == user.tg_id:
        return

    had_subscription = (
        await session.execute(select(func.count(Subscription.id)).where(Subscription.user_id == user.id))
    ).scalar_one()
    had_payment = (
        await session.execute(select(func.count(Payment.id)).where(Payment.user_id == user.id))
    ).scalar_one()
    if had_subscription or had_payment:
        return

    referrer = (await session.execute(select(User).where(User.tg_id == int(ref_tg_id)))).scalar_one_or_none()
    if referrer is not None:
        user.referred_by = referrer.id


async def on_plan_paid(bot: Bot, panel_client: H1PanelClient, user_id: int) -> None:
    """Вызывается после успешной оплаты подписки. Ошибки здесь не должны
    ломать саму покупку — поэтому всё в try."""
    try:
        await _credit(bot, panel_client, user_id)
    except Exception:
        logger.exception("Referral credit failed for user_id=%s", user_id)


async def _credit(bot: Bot, panel_client: H1PanelClient, user_id: int) -> None:
    async with get_session() as session:
        user = await session.get(User, user_id, with_for_update=True)
        if user is None or user.referred_by is None or user.referral_counted:
            return
        referrer = await session.get(User, user.referred_by, with_for_update=True)
        if referrer is None:
            return

        user.referral_counted = True
        referrer.referral_friends += 1
        friends = referrer.referral_friends
        referrer_tg_id = referrer.tg_id
        referrer_id = referrer.id
        await session.commit()

    if friends % REFERRALS_FOR_REWARD != 0:
        left = REFERRALS_FOR_REWARD - friends % REFERRALS_FOR_REWARD
        await _notify(bot, referrer_tg_id, texts.REFERRAL_FRIEND_PAID.format(
            progress=progress_bar(friends), done=friends % REFERRALS_FOR_REWARD,
            total=REFERRALS_FOR_REWARD, left=left,
        ))
    granted = await grant_pending_rewards(bot, panel_client, referrer_id)
    if friends % REFERRALS_FOR_REWARD == 0 and not granted:
        # месяц заработан, но панель сейчас недоступна — скажем, что он не потерян
        await _notify(bot, referrer_tg_id, texts.REFERRAL_REWARD_DELAYED.format(total=REFERRALS_FOR_REWARD))


def pending_rewards(user: User) -> int:
    return user.referral_friends // REFERRALS_FOR_REWARD - user.referral_rewards


async def grant_pending_rewards(bot: Bot, panel_client: H1PanelClient, user_id: int) -> bool:
    """Выдаёт заработанные, но ещё не выданные бесплатные месяцы.

    Если панель недоступна — награда остаётся «должна» и выдастся при
    следующем вызове (новый друг или открытие экрана рефералки).
    Возвращает True, если что-то выдано.
    """
    async with get_session() as session:
        user = await session.get(User, user_id, with_for_update=True)
        if user is None or pending_rewards(user) <= 0:
            return False

        days = REFERRAL_REWARD_DAYS * pending_rewards(user)
        marzban_username = user.marzban_username or marzban_username_for(user.tg_id)
        try:
            key = await panel_client.upsert_user(
                username=marzban_username, days=days, traffic_gb=None, device_limit=device_limit_for(user)
            )
        except H1PanelError:
            logger.exception("Referral reward failed for tg_id=%s", user.tg_id)
            return False

        user.marzban_username = marzban_username
        subscription = await record_subscription(session, user.id, plan_id="referral", days=days)
        carry_extra_devices(user, subscription.expires_at)
        user.referral_rewards = user.referral_friends // REFERRALS_FOR_REWARD
        tg_id = user.tg_id
        expires = subscription.expires_at.strftime("%d.%m.%Y")
        await session.commit()

    await _notify(
        bot, tg_id, texts.REFERRAL_REWARD.format(days=days, expires=expires, key=key),
        reply_markup=back_to_menu(keep_message=True),
    )
    return True


def progress_bar(friends: int) -> str:
    done = friends % REFERRALS_FOR_REWARD
    return "●" * done + "○" * (REFERRALS_FOR_REWARD - done)


async def _notify(bot: Bot, tg_id: int, text: str, **kwargs) -> None:
    try:
        await bot.send_message(tg_id, text, **kwargs)
    except (TelegramForbiddenError, TelegramBadRequest):
        logger.info("Could not notify tg_id=%s about referral", tg_id)

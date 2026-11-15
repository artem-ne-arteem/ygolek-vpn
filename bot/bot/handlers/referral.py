from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import texts
from bot.db.repo import get_or_create_user
from bot.db.session import get_session
from bot.h1panel.client import H1PanelClient
from bot.keyboards import referral_menu
from bot.plans import REFERRALS_FOR_REWARD
from bot.referrals import grant_pending_rewards, progress_bar, referral_link
from bot.telegram_utils import safe_answer, show_screen

router = Router()


@router.callback_query(F.data == "ref:show")
async def show_referral(callback: CallbackQuery, panel_client: H1PanelClient) -> None:
    await safe_answer(callback)

    async with get_session() as session:
        user = await get_or_create_user(session, callback.from_user)
        await session.commit()
        user_id = user.id

    # заработанный, но не выданный месяц (панель была недоступна) — выдаём сейчас
    await grant_pending_rewards(callback.bot, panel_client, user_id)

    async with get_session() as session:
        user = await get_or_create_user(session, callback.from_user)
        friends, rewards, tg_id = user.referral_friends, user.referral_rewards, user.tg_id

    link = referral_link((await callback.bot.me()).username, tg_id)
    text = texts.REFERRAL_SCREEN.format(
        total=REFERRALS_FOR_REWARD,
        progress=progress_bar(friends),
        done=friends % REFERRALS_FOR_REWARD,
        friends=friends,
        rewards=rewards,
        link=link,
    )
    await show_screen(callback, text, referral_menu(link, texts.REFERRAL_SHARE_TEXT))

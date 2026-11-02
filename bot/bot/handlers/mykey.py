import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import texts
from bot.db.repo import get_active_subscription, get_or_create_user
from bot.db.session import get_session
from bot.keyboards import back_to_menu
from bot.h1panel.client import H1PanelClient, H1PanelError
from bot.telegram_utils import safe_answer

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "mykey:show")
async def show_key(callback: CallbackQuery, panel_client: H1PanelClient) -> None:
    await safe_answer(callback)

    async with get_session() as session:
        user = await get_or_create_user(session, callback.from_user)
        subscription = await get_active_subscription(session, user.id)

    if subscription is None or user.marzban_username is None:
        await callback.message.answer(texts.MY_KEY_NOT_FOUND, reply_markup=back_to_menu())
        return

    try:
        key = await panel_client.get_subscription_url(user.marzban_username)
    except H1PanelError:
        logger.exception("Failed to fetch key for tg_id=%s", user.tg_id)
        await callback.message.answer(texts.MARZBAN_ERROR)
        return

    if key is None:
        await callback.message.answer(texts.MY_KEY_NOT_FOUND, reply_markup=back_to_menu())
        return

    await callback.message.answer(
        texts.MY_KEY.format(expires=subscription.expires_at.strftime("%d.%m.%Y"), key=key),
        reply_markup=back_to_menu(),
    )

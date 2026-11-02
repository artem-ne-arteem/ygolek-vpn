import datetime as dt
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import texts
from bot.db.repo import get_active_subscription, get_or_create_user
from bot.db.session import get_session
from bot.devices import device_limit_for
from bot.h1panel.client import H1PanelClient, H1PanelError
from bot.keyboards import back_to_menu, key_menu, plans_menu
from bot.telegram_utils import safe_answer, show_screen

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "mykey:show")
async def show_key(callback: CallbackQuery, panel_client: H1PanelClient) -> None:
    await safe_answer(callback)

    async with get_session() as session:
        user = await get_or_create_user(session, callback.from_user)
        subscription = await get_active_subscription(session, user.id)
        await session.commit()

    if subscription is None or user.marzban_username is None:
        await show_screen(callback, texts.MY_KEY_NOT_FOUND, plans_menu())
        return

    try:
        key = await panel_client.get_subscription_url(user.marzban_username)
    except H1PanelError:
        logger.exception("Failed to fetch key for tg_id=%s", user.tg_id)
        await show_screen(callback, texts.MARZBAN_ERROR, back_to_menu())
        return

    if key is None:
        await show_screen(callback, texts.MY_KEY_NOT_FOUND, plans_menu())
        return

    await show_screen(
        callback,
        texts.MY_KEY.format(
            expires=subscription.expires_at.strftime("%d.%m.%Y"),
            left=texts.time_left_label(subscription.expires_at - dt.datetime.utcnow()),
            key=key,
            devices=device_limit_for(user),
        ),
        key_menu(),
    )

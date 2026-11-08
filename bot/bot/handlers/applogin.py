"""Вход в приложение Ygolek VPN: приложение показывает ссылку
t.me/<бот>?start=app_<code>, пользователь подтверждает вход здесь."""

import datetime as dt
import html
import logging

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot import texts
from bot.db.models import AppLogin
from bot.db.repo import get_or_create_user
from bot.db.session import get_session
from bot.telegram_utils import safe_answer

logger = logging.getLogger(__name__)
router = Router()

APP_START_PREFIX = "app_"
# Сколько живёт запрос на вход (столько же ждёт приложение)
LOGIN_TTL = dt.timedelta(minutes=10)


def _confirm_menu(code: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Войти", callback_data=f"applogin:ok:{code}")
    builder.button(text="Отмена", callback_data=f"applogin:no:{code}")
    builder.adjust(2)
    return builder.as_markup()


async def _pending_login(session, code: str) -> AppLogin | None:
    result = await session.execute(select(AppLogin).where(AppLogin.code == code).with_for_update())
    login = result.scalar_one_or_none()
    if login is None or login.status != "pending":
        return None
    if dt.datetime.utcnow() - login.created_at > LOGIN_TTL:
        return None
    return login


@router.message(CommandStart(deep_link=True, magic=F.args.startswith(APP_START_PREFIX)))
async def app_login_request(message: Message, command: CommandObject) -> None:
    code = command.args.removeprefix(APP_START_PREFIX)
    async with get_session() as session:
        login = await _pending_login(session, code)
        await session.commit()

    if login is None:
        await message.answer(texts.APP_LOGIN_EXPIRED)
        return
    device = html.escape(login.device or "новое устройство")
    await message.answer(texts.APP_LOGIN_CONFIRM.format(device=device), reply_markup=_confirm_menu(code))


@router.callback_query(F.data.startswith("applogin:"))
async def app_login_answer(callback: CallbackQuery) -> None:
    await safe_answer(callback)
    _, action, code = callback.data.split(":", 2)

    async with get_session() as session:
        login = await _pending_login(session, code)
        if login is None:
            await session.commit()
            await callback.message.edit_text(texts.APP_LOGIN_EXPIRED)
            return
        if action == "ok":
            user = await get_or_create_user(session, callback.from_user)
            login.user_id = user.id
            login.status = "approved"
            login.approved_at = dt.datetime.utcnow()
        else:
            login.status = "denied"
        device = html.escape(login.device or "устройство")
        await session.commit()

    if action == "ok":
        logger.info("App login approved for tg_id=%s on %s", callback.from_user.id, device)
        await callback.message.edit_text(texts.APP_LOGIN_DONE.format(device=device))
    else:
        await callback.message.edit_text(texts.APP_LOGIN_DENIED)

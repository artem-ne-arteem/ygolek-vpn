from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.types import User as TgUser

from bot import texts
from bot.db.repo import get_active_subscription, get_or_create_user
from bot.db.session import get_session
from bot.keyboards import back_to_menu, main_menu
from bot.telegram_utils import safe_answer, show_screen

router = Router()

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.jpg"


async def _menu_for(tg_user: TgUser) -> tuple[str, object]:
    async with get_session() as session:
        user = await get_or_create_user(session, tg_user)
        subscription = await get_active_subscription(session, user.id)
        await session.commit()

    expires_at = subscription.expires_at if subscription else None
    return texts.welcome(expires_at), main_menu(has_subscription=subscription is not None)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text, markup = await _menu_for(message.from_user)
    await message.answer_photo(FSInputFile(LOGO_PATH), caption=text, reply_markup=markup)


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    text, markup = await _menu_for(message.from_user)
    await message.answer(text, reply_markup=markup)


@router.callback_query(F.data == "menu:show")
async def show_menu(callback: CallbackQuery) -> None:
    await safe_answer(callback)
    text, markup = await _menu_for(callback.from_user)
    await show_screen(callback, text, markup)


@router.callback_query(F.data == "menu:new")
async def show_menu_new_message(callback: CallbackQuery) -> None:
    """Меню отдельным сообщением — чтобы не затереть сообщение с ключом."""
    await safe_answer(callback)
    text, markup = await _menu_for(callback.from_user)
    await callback.bot.send_message(callback.from_user.id, text, reply_markup=markup)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP)


@router.callback_query(F.data == "help:show")
async def show_help(callback: CallbackQuery) -> None:
    await safe_answer(callback)
    await show_screen(callback, texts.HELP, back_to_menu())

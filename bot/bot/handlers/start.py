from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot import texts
from bot.keyboards import main_menu
from bot.telegram_utils import safe_answer

router = Router()

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.jpg"


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer_photo(
        FSInputFile(LOGO_PATH),
        caption=texts.WELCOME,
        reply_markup=main_menu(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await message.answer(texts.WELCOME, reply_markup=main_menu())


@router.callback_query(F.data == "menu:show")
async def show_menu(callback: CallbackQuery) -> None:
    await safe_answer(callback)
    await callback.message.answer(texts.WELCOME, reply_markup=main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP)

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.keyboards import legal_menu
from bot.telegram_utils import safe_answer

router = Router()


@router.message(Command("legal"))
async def cmd_legal(message: Message) -> None:
    await message.answer(texts.LEGAL, reply_markup=legal_menu())


@router.callback_query(F.data == "legal:show")
async def show_legal(callback: CallbackQuery) -> None:
    await safe_answer(callback)
    await callback.message.answer(texts.LEGAL, reply_markup=legal_menu())

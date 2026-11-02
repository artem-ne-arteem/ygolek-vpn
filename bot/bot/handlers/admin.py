from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot import texts
from bot.config import Config
from bot.db.repo import get_stats
from bot.db.session import get_session

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message, config: Config) -> None:
    if message.from_user.id not in config.admin_ids:
        return

    async with get_session() as session:
        stats = await get_stats(session)

    await message.answer(texts.STATS.format(**stats))

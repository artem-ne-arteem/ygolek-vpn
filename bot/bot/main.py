import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import load_config
from bot.db.session import init_db
from bot.handlers import build_root_router
from bot.h1panel.client import H1PanelClient
from bot.reminders import reminder_loop


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    config = load_config()
    await init_db(config)

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(build_root_router())

    panel_client = H1PanelClient(config)
    reminder_task = asyncio.create_task(reminder_loop(bot))
    try:
        await dp.start_polling(bot, panel_client=panel_client, config=config)
    finally:
        reminder_task.cancel()
        await panel_client.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging
import sys
from pathlib import Path

# Хостинг может запускать бота из корня репозитория (`python -m bot.bot.main`),
# а не из папки bot/ — тогда пакет `bot` указывает на bot/, а не на bot/bot/.
# Добавляем bot/ в sys.path и забываем уже импортированный «неправильный» `bot`,
# чтобы `from bot.xxx import ...` работал в обоих случаях.
if __package__ != "bot":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys.modules.pop("bot", None)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import MenuButtonWebApp, WebAppInfo

from bot import texts
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

    # Кнопка «Приложение» слева от поля ввода — открывает мини-апп
    if config.webapp_url:
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(text="Приложение", web_app=WebAppInfo(url=config.webapp_url))
            )
        except Exception:
            logging.exception("Failed to set the mini app menu button")

    # Описание бота («Что умеет этот бот?») и короткое описание в профиле —
    # задаём из кода, чтобы текст был под контролем, а не правился в BotFather
    try:
        await bot.set_my_description(texts.bot_description())
        await bot.set_my_short_description(texts.bot_short_description())
    except Exception:
        logging.exception("Failed to set the bot description")

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

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


async def show_screen(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
    """Перерисовывает сообщение с кнопкой вместо отправки нового.

    Так меню живёт в одном сообщении и не засоряет чат. Если сообщение
    отредактировать нельзя (слишком старое, удалено) — шлём новое.
    """
    message = callback.message
    try:
        if getattr(message, "photo", None):
            # стартовое сообщение — фото с логотипом, у него редактируется подпись
            await message.edit_caption(caption=text, reply_markup=markup)
        else:
            await message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=markup)
    except AttributeError:
        # InaccessibleMessage (старше 48 часов) — редактировать нечего
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=markup)


async def safe_answer(callback: CallbackQuery, *args, **kwargs) -> None:
    """callback.answer(), но не роняет хендлер, если callback уже протух.

    Актуально после рестарта бота: пока он был недоступен, пользователь мог
    успеть нажать кнопку, и Telegram отклонит answer() как "too old". Само
    действие (выдача ключа и т.п.) в этот момент уже должно было отработать —
    терять его из-за истёкшего "тика" загрузки не нужно.
    """
    try:
        await callback.answer(*args, **kwargs)
    except TelegramBadRequest:
        logger.debug("callback.answer() failed (stale callback query), ignoring")

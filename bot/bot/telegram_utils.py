import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)


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

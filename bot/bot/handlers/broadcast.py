"""Рассылка от админа всем, кто запускал бота.

Админ присылает сообщение (текст, фото, видео — с форматированием), бот
спрашивает подтверждение и копирует его каждому пользователю. Рассылка идёт
в фоне со скоростью ~20 сообщений в секунду (лимит Telegram — 30), в конце
админ получает отчёт.
"""

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db.repo import get_all_tg_ids
from bot.db.session import get_session
from bot.handlers.admin import IsAdmin
from bot.keyboards import admin_menu, broadcast_cancel_menu, broadcast_confirm_menu
from bot.telegram_utils import safe_answer

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

SEND_INTERVAL = 0.05  # 20 сообщений в секунду
# держим ссылки на фоновые рассылки, чтобы их не собрал сборщик мусора
_running: set[asyncio.Task] = set()


class BroadcastStates(StatesGroup):
    waiting_message = State()
    waiting_confirm = State()


@router.callback_query(F.data == "admin:broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(callback)
    await state.set_state(BroadcastStates.waiting_message)
    await callback.message.answer(texts.BROADCAST_ASK, reply_markup=broadcast_cancel_menu())


@router.message(StateFilter(BroadcastStates.waiting_message))
async def broadcast_message(message: Message, state: FSMContext) -> None:
    async with get_session() as session:
        total = len(await get_all_tg_ids(session))

    await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(BroadcastStates.waiting_confirm)
    await message.reply(texts.BROADCAST_CONFIRM.format(total=total), reply_markup=broadcast_confirm_menu())


@router.callback_query(StateFilter(BroadcastStates.waiting_confirm), F.data == "admin:broadcast:send")
async def broadcast_send(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    # состояние сбрасываем сразу — повторное нажатие не запустит вторую рассылку
    await state.clear()
    await safe_answer(callback)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(texts.BROADCAST_STARTED)

    task = asyncio.create_task(
        run_broadcast(bot, data["from_chat_id"], data["message_id"], report_chat_id=callback.from_user.id)
    )
    _running.add(task)
    task.add_done_callback(_running.discard)


@router.callback_query(F.data == "admin:broadcast:cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(callback)
    await state.clear()
    await callback.message.answer(texts.BROADCAST_CANCELLED, reply_markup=admin_menu())


async def run_broadcast(bot: Bot, from_chat_id: int, message_id: int, report_chat_id: int) -> None:
    async with get_session() as session:
        tg_ids = await get_all_tg_ids(session)

    sent = blocked = failed = 0
    for tg_id in tg_ids:
        result = await _copy(bot, tg_id, from_chat_id, message_id)
        if result == "sent":
            sent += 1
        elif result == "blocked":
            blocked += 1
        else:
            failed += 1
        await asyncio.sleep(SEND_INTERVAL)

    logger.info("Broadcast done: sent=%s blocked=%s failed=%s", sent, blocked, failed)
    await bot.send_message(
        report_chat_id,
        texts.BROADCAST_DONE.format(sent=sent, blocked=blocked, failed=failed, total=len(tg_ids)),
        reply_markup=admin_menu(),
    )


async def _copy(bot: Bot, tg_id: int, from_chat_id: int, message_id: int) -> str:
    for _ in range(3):
        try:
            await bot.copy_message(chat_id=tg_id, from_chat_id=from_chat_id, message_id=message_id)
            return "sent"
        except TelegramRetryAfter as exc:
            # Telegram просит подождать — ждём и пробуем снова
            await asyncio.sleep(exc.retry_after + 1)
        except TelegramForbiddenError:
            return "blocked"
        except TelegramBadRequest:
            logger.info("Broadcast: could not deliver to tg_id=%s", tg_id, exc_info=True)
            return "failed"
    return "failed"

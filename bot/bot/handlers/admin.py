import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, Filter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.admin_access import is_admin
from bot.config import Config
from bot.db.repo import (
    find_user_by_username,
    get_or_create_user_by_tg_id,
    get_stats,
    marzban_username_for,
    record_subscription,
)
from bot.db.session import get_session
from bot.h1panel.client import H1PanelClient, H1PanelError
from bot.keyboards import admin_cancel_menu, admin_grant_days_menu, admin_menu, back_to_menu
from bot.telegram_utils import safe_answer

logger = logging.getLogger(__name__)
router = Router()

MAX_GRANT_DAYS = 3650


class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery, config: Config) -> bool:
        return is_admin(event.from_user, config)


# Всё в этом роутере — только для админов; остальным бот просто не отвечает
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class GrantStates(StatesGroup):
    waiting_user = State()
    waiting_days = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.ADMIN_MENU, reply_markup=admin_menu())


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    await message.answer(await _stats_text())


@router.callback_query(F.data == "admin:stats")
async def show_stats(callback: CallbackQuery) -> None:
    await safe_answer(callback)
    await callback.message.answer(await _stats_text(), reply_markup=admin_menu())


async def _stats_text() -> str:
    async with get_session() as session:
        stats = await get_stats(session)
    return texts.STATS.format(**stats)


@router.callback_query(F.data == "admin:cancel")
async def cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(callback)
    await state.clear()
    await callback.message.answer(texts.ADMIN_GRANT_CANCELLED, reply_markup=admin_menu())


@router.callback_query(F.data == "admin:grant")
async def grant_start(callback: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(callback)
    await state.set_state(GrantStates.waiting_user)
    await callback.message.answer(texts.ADMIN_GRANT_ASK_USER, reply_markup=admin_cancel_menu())


@router.message(StateFilter(GrantStates.waiting_user), F.text)
async def grant_user(message: Message, state: FSMContext) -> None:
    query = message.text.strip()

    if query.lstrip("-").isdigit():
        tg_id = int(query)
        who = f"<code>{tg_id}</code>"
    else:
        async with get_session() as session:
            user = await find_user_by_username(session, query)
        if user is None:
            await message.answer(
                texts.ADMIN_GRANT_USER_NOT_FOUND.format(query=query),
                reply_markup=admin_cancel_menu(),
            )
            return
        tg_id = user.tg_id
        who = f"@{user.username} (<code>{tg_id}</code>)"

    await state.update_data(tg_id=tg_id, who=who)
    await state.set_state(GrantStates.waiting_days)
    await message.answer(texts.ADMIN_GRANT_ASK_DAYS.format(who=who), reply_markup=admin_grant_days_menu())


@router.callback_query(StateFilter(GrantStates.waiting_days), F.data.startswith("admin:days:"))
async def grant_days_button(
    callback: CallbackQuery, state: FSMContext, panel_client: H1PanelClient, bot: Bot
) -> None:
    await safe_answer(callback)
    days = int(callback.data.removeprefix("admin:days:"))
    await _grant(callback.message, state, panel_client, bot, days)


@router.message(StateFilter(GrantStates.waiting_days), F.text)
async def grant_days_text(message: Message, state: FSMContext, panel_client: H1PanelClient, bot: Bot) -> None:
    text = message.text.strip()
    if not text.isdigit() or not 1 <= int(text) <= MAX_GRANT_DAYS:
        await message.answer(texts.ADMIN_GRANT_BAD_DAYS, reply_markup=admin_grant_days_menu())
        return
    await _grant(message, state, panel_client, bot, int(text))


async def _grant(reply_to: Message, state: FSMContext, panel_client: H1PanelClient, bot: Bot, days: int) -> None:
    data = await state.get_data()
    tg_id: int = data["tg_id"]
    who: str = data["who"]

    async with get_session() as session:
        user = await get_or_create_user_by_tg_id(session, tg_id)
        marzban_username = user.marzban_username or marzban_username_for(user.tg_id)

        try:
            key = await panel_client.upsert_user(username=marzban_username, days=days, traffic_gb=None)
        except H1PanelError:
            logger.exception("Admin grant failed for tg_id=%s", tg_id)
            await reply_to.answer(texts.MARZBAN_ERROR, reply_markup=admin_menu())
            await state.clear()
            return

        user.marzban_username = marzban_username
        subscription = await record_subscription(session, user.id, plan_id="admin", days=days)
        await session.commit()
        expires = subscription.expires_at.strftime("%d.%m.%Y")

    await state.clear()

    result = texts.ADMIN_GRANT_DONE.format(who=who, expires=expires, key=key)
    try:
        await bot.send_message(
            tg_id,
            texts.GIFT_ISSUED.format(expires=expires, key=key),
            reply_markup=back_to_menu(keep_message=True),
        )
    except (TelegramForbiddenError, TelegramBadRequest):
        logger.info("Could not deliver granted key to tg_id=%s", tg_id)
        result += texts.ADMIN_GRANT_NOT_NOTIFIED

    await reply_to.answer(result, reply_markup=admin_menu())

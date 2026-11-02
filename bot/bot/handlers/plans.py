from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import texts
from bot.capacity import can_buy
from bot.config import Config
from bot.db.repo import get_or_create_user
from bot.db.session import get_session
from bot.keyboards import back_to_menu, plans_menu
from bot.payments import get_provider
from bot.plans import DEVICE_LIMIT, get_plan
from bot.telegram_utils import safe_answer, show_screen

router = Router()


async def _plan_allowed(callback: CallbackQuery, config: Config) -> bool:
    async with get_session() as session:
        user = await get_or_create_user(session, callback.from_user)
        allowed = await can_buy(session, config, user, "plan")
        await session.commit()
    return allowed


@router.callback_query(F.data == "plans:show")
async def show_plans(callback: CallbackQuery, config: Config) -> None:
    await safe_answer(callback)
    if not await _plan_allowed(callback, config):
        await show_screen(callback, texts.CAPACITY_FULL, back_to_menu())
        return
    await show_screen(callback, texts.PLANS_HEADER.format(devices=DEVICE_LIMIT), plans_menu())


@router.callback_query(F.data.startswith("plan:select:"))
async def select_plan(callback: CallbackQuery, config: Config) -> None:
    plan_id = callback.data.removeprefix("plan:select:")
    plan = get_plan(plan_id)
    if plan is None:
        await safe_answer(callback, "Тариф не найден", show_alert=True)
        return

    if not await _plan_allowed(callback, config):
        await safe_answer(callback, texts.CAPACITY_FULL_SHORT, show_alert=True)
        return

    await safe_answer(callback)
    provider = get_provider("stars")
    await provider.send_invoice(callback.bot, callback.from_user.id, plan)

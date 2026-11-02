from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import texts
from bot.keyboards import plans_menu
from bot.payments import get_provider
from bot.plans import DEVICE_LIMIT, get_plan
from bot.telegram_utils import safe_answer, show_screen

router = Router()


@router.callback_query(F.data == "plans:show")
async def show_plans(callback: CallbackQuery) -> None:
    await safe_answer(callback)
    await show_screen(callback, texts.PLANS_HEADER.format(devices=DEVICE_LIMIT), plans_menu())


@router.callback_query(F.data.startswith("plan:select:"))
async def select_plan(callback: CallbackQuery) -> None:
    plan_id = callback.data.removeprefix("plan:select:")
    plan = get_plan(plan_id)
    if plan is None:
        await safe_answer(callback, "Тариф не найден", show_alert=True)
        return

    await safe_answer(callback)
    provider = get_provider("stars")
    await provider.send_invoice(callback.bot, callback.from_user.id, plan)

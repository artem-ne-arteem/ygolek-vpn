import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import texts
from bot.capacity import can_buy
from bot.card_orders import create_card_order
from bot.config import Config
from bot.db.repo import get_or_create_user
from bot.db.session import get_session
from bot.keyboards import back_to_menu, card_payment_menu, plans_menu
from bot.payments import get_provider
from bot.payments.platega import PlategaClient, PlategaError
from bot.plans import DEVICE_LIMIT, PLANS, get_plan
from bot.telegram_utils import safe_answer, show_screen

logger = logging.getLogger(__name__)
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
    prices = "\n".join(
        texts.PLAN_PRICE_LINE.format(title=p.title, rub=p.price_rub, stars=p.price_stars) for p in PLANS
    )
    await show_screen(callback, texts.PLANS_HEADER.format(devices=DEVICE_LIMIT, prices=prices), plans_menu())


@router.callback_query(F.data.startswith("plan:card:"))
async def pay_by_card(callback: CallbackQuery, config: Config, platega_client: PlategaClient) -> None:
    if not platega_client.enabled:
        # ключи Platega не заданы — заглушка вместо платежа
        await safe_answer(callback, texts.CARD_PAYMENT_STUB, show_alert=True)
        return

    plan = get_plan(callback.data.removeprefix("plan:card:"))
    if plan is None:
        await safe_answer(callback, "Тариф не найден", show_alert=True)
        return
    if not await _plan_allowed(callback, config):
        await safe_answer(callback, texts.CAPACITY_FULL_SHORT, show_alert=True)
        return

    await safe_answer(callback)
    async with get_session() as session:
        user = await get_or_create_user(session, callback.from_user)
        await session.commit()

    bot_url = f"https://t.me/{(await callback.bot.me()).username}"
    try:
        payment = await create_card_order(platega_client, user, plan, return_url=bot_url)
    except PlategaError:
        logger.exception("Failed to create Platega payment for tg_id=%s", callback.from_user.id)
        await callback.bot.send_message(callback.from_user.id, texts.CARD_PAYMENT_FAILED)
        return

    await callback.bot.send_message(
        callback.from_user.id,
        texts.CARD_PAYMENT_LINK.format(title=plan.title, price=plan.price_rub),
        reply_markup=card_payment_menu(payment.url),
    )


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

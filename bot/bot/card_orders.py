"""Оплата картой / СБП через Platega: создание заказа и выдача подписки.

Путь заказа: бот или сайт создаёт card_orders (pending) и ссылку Platega →
покупатель платит → колбэк Platega на сайте помечает заказ paid (а если
колбэк потерялся — это сделает card_orders_loop, сверив статус через API) →
card_orders_loop выдаёт подписку и присылает ключ в Telegram (fulfilled).
"""

import asyncio
import datetime as dt
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import select

from bot import texts
from bot.db.models import CardOrder, Payment, User
from bot.db.repo import marzban_username_for, record_subscription
from bot.db.session import get_session
from bot.devices import carry_extra_devices, device_limit_for
from bot.h1panel.client import H1PanelClient, H1PanelError
from bot.keyboards import back_to_menu
from bot.payments.platega import PlategaClient, PlategaError, PlategaPayment
from bot.plans import Plan, get_plan

logger = logging.getLogger(__name__)

LOOP_INTERVAL = dt.timedelta(seconds=15)
# Сверяем статус pending-заказов с Platega раз в минуту и только по свежим:
# ссылка на оплату живёт 15 минут, час — с запасом
STATUS_CHECK_EVERY = 4  # итераций цикла
STATUS_CHECK_WINDOW = dt.timedelta(hours=1)


async def create_card_order(platega: PlategaClient, user: User, plan: Plan, return_url: str) -> PlategaPayment:
    """Заводит заказ и ссылку на оплату. Бросает PlategaError."""
    async with get_session() as session:
        order = CardOrder(user_id=user.id, plan_id=plan.id, amount_rub=plan.price_rub, source="bot")
        session.add(order)
        await session.commit()

        try:
            payment = await platega.create_payment(
                amount_rub=plan.price_rub,
                description=texts.CARD_PAYMENT_DESCRIPTION.format(title=plan.title),
                order_id=order.id,
                tg_id=user.tg_id,
                username=user.username,
                return_url=return_url,
            )
        except PlategaError:
            order.status = "canceled"
            await session.commit()
            raise

        order.transaction_id = payment.transaction_id
        await session.commit()
    return payment


async def card_orders_loop(bot: Bot, panel_client: H1PanelClient, platega: PlategaClient) -> None:
    iteration = 0
    while True:
        try:
            if platega.enabled and iteration % STATUS_CHECK_EVERY == 0:
                await _check_pending(platega)
            await _fulfil_paid(bot, panel_client)
        except Exception:
            logger.exception("Card orders loop iteration failed")
        iteration += 1
        await asyncio.sleep(LOOP_INTERVAL.total_seconds())


async def _check_pending(platega: PlategaClient) -> None:
    """Подстраховка колбэка: сами спрашиваем у Platega статус свежих заказов."""
    since = dt.datetime.utcnow() - STATUS_CHECK_WINDOW
    async with get_session() as session:
        orders = (
            await session.execute(
                select(CardOrder).where(
                    CardOrder.status == "pending",
                    CardOrder.transaction_id.is_not(None),
                    CardOrder.created_at >= since,
                )
            )
        ).scalars().all()

        for order in orders:
            try:
                tx = await platega.get_status(order.transaction_id)
            except PlategaError:
                logger.warning("Could not check Platega status for order %s", order.id, exc_info=True)
                continue
            apply_platega_status(order, tx.get("status"), (tx.get("paymentDetails") or {}).get("amount"))
        await session.commit()


def apply_platega_status(order: CardOrder, status: str | None, amount: float | None) -> None:
    if order.status != "pending":
        return
    if status == "CONFIRMED":
        if amount is not None and float(amount) + 0.01 < order.amount_rub:
            logger.error("Order %s confirmed for %s RUB, expected %s", order.id, amount, order.amount_rub)
            return
        order.status = "paid"
        order.paid_at = dt.datetime.utcnow()
    elif status in ("CANCELED", "CHARGEBACKED"):
        order.status = "canceled"


async def _fulfil_paid(bot: Bot, panel_client: H1PanelClient) -> None:
    async with get_session() as session:
        order_ids = (
            await session.execute(select(CardOrder.id).where(CardOrder.status == "paid").order_by(CardOrder.id))
        ).scalars().all()

    for order_id in order_ids:
        await _fulfil_one(bot, panel_client, order_id)


async def _fulfil_one(bot: Bot, panel_client: H1PanelClient, order_id: int) -> None:
    async with get_session() as session:
        order = await session.get(CardOrder, order_id, with_for_update=True)
        if order is None or order.status != "paid":
            return
        user = await session.get(User, order.user_id)
        plan = get_plan(order.plan_id)
        if user is None or plan is None:
            logger.error("Card order %s: unknown user or plan %s", order.id, order.plan_id)
            return

        marzban_username = user.marzban_username or marzban_username_for(user.tg_id)
        try:
            key = await panel_client.upsert_user(
                username=marzban_username,
                days=plan.days,
                traffic_gb=plan.traffic_gb,
                device_limit=device_limit_for(user),
            )
        except H1PanelError:
            # Деньги получены — заказ остаётся paid, повторим на следующей итерации
            order.fulfil_attempts += 1
            first_failure = order.fulfil_attempts == 1
            tg_id = user.tg_id
            await session.commit()
            if first_failure:
                logger.exception("Failed to issue key for card order %s", order_id)
                await _notify(bot, tg_id, texts.MARZBAN_ERROR)
            return

        user.marzban_username = marzban_username
        subscription = await record_subscription(session, user.id, plan_id=plan.id, days=plan.days)
        carry_extra_devices(user, subscription.expires_at)
        order.status = "fulfilled"
        order.fulfilled_at = dt.datetime.utcnow()
        session.add(
            Payment(
                user_id=user.id,
                plan_id=plan.id,
                provider="platega",
                amount=order.amount_rub,
                currency="RUB",
                status="paid",
                telegram_charge_id=order.transaction_id,
            )
        )
        tg_id = user.tg_id
        await session.commit()
        expires = subscription.expires_at.strftime("%d.%m.%Y")

    await _notify(
        bot,
        tg_id,
        texts.PAYMENT_SUCCESS.format(expires=expires, key=key),
        reply_markup=back_to_menu(keep_message=True),
    )


async def _notify(bot: Bot, tg_id: int, text: str, **kwargs) -> None:
    # Купивший на сайте мог ни разу не запускать бота — тогда ключ он увидит
    # в личном кабинете, а сообщение просто не дойдёт
    try:
        await bot.send_message(tg_id, text, **kwargs)
    except (TelegramForbiddenError, TelegramBadRequest):
        logger.info("Could not message tg_id=%s about card order", tg_id)

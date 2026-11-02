import logging

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery, SuccessfulPayment

from bot import texts
from bot.capacity import can_buy
from bot.config import Config
from bot.db.models import Payment, User
from bot.db.repo import get_active_subscription, get_or_create_user, marzban_username_for, record_subscription
from bot.db.session import get_session
from bot.devices import add_extra_device, carry_extra_devices, device_limit_for
from bot.handlers.devices import DEVICE_PAYLOAD
from bot.handlers.gift import GIFT_PAYLOAD_PREFIX, gift_paid, gift_purchase_error
from bot.keyboards import back_to_menu
from bot.h1panel.client import H1PanelClient, H1PanelError
from bot.plans import MAX_EXTRA_DEVICES, get_plan

logger = logging.getLogger(__name__)
router = Router()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery, config: Config) -> None:
    """Последняя проверка перед списанием звёзд — счёт мог быть выставлен давно
    (или с сайта/мини-аппа), а мощности с тех пор закончиться."""
    payload = pre_checkout_query.invoice_payload

    if payload.startswith(GIFT_PAYLOAD_PREFIX):
        error = await gift_purchase_error(config, payload)
        if error:
            await pre_checkout_query.answer(ok=False, error_message=error)
        else:
            await pre_checkout_query.answer(ok=True)
        return

    async with get_session() as session:
        user = await get_or_create_user(session, pre_checkout_query.from_user)
        await session.commit()

        if payload == DEVICE_PAYLOAD:
            if await get_active_subscription(session, user.id) is None:
                error = "Подписка закончилась — сначала продли её"
            elif user.active_extra_devices() >= MAX_EXTRA_DEVICES:
                error = "Достигнут максимум устройств"
            elif not await can_buy(session, config, user, "device"):
                error = texts.CAPACITY_FULL_SHORT
            else:
                error = None
        elif get_plan(payload.removeprefix("plan:")) is None:
            error = "Тариф больше не доступен"
        elif not await can_buy(session, config, user, "plan"):
            error = texts.CAPACITY_FULL_SHORT
        else:
            error = None

    if error:
        await pre_checkout_query.answer(ok=False, error_message=error)
    else:
        await pre_checkout_query.answer(ok=True)


def _payment(user: User, plan_id: str, sp: SuccessfulPayment, status: str) -> Payment:
    return Payment(
        user_id=user.id,
        plan_id=plan_id,
        provider="stars",
        amount=sp.total_amount,
        currency=sp.currency,
        status=status,
        telegram_charge_id=sp.telegram_payment_charge_id,
    )


@router.message(F.successful_payment)
async def successful_payment(message: Message, panel_client: H1PanelClient) -> None:
    payload = message.successful_payment.invoice_payload
    if payload == DEVICE_PAYLOAD:
        await _device_paid(message, panel_client)
    elif payload.startswith(GIFT_PAYLOAD_PREFIX):
        await gift_paid(message)
    else:
        await _plan_paid(message, panel_client)


async def _plan_paid(message: Message, panel_client: H1PanelClient) -> None:
    sp = message.successful_payment
    plan = get_plan(sp.invoice_payload.removeprefix("plan:"))
    if plan is None:
        return

    async with get_session() as session:
        user = await get_or_create_user(session, message.from_user)
        marzban_username = user.marzban_username or marzban_username_for(user.tg_id)

        # Деньги через Telegram уже списаны к этому моменту — что бы ни
        # случилось с панелью дальше, платёж обязательно должен попасть в БД,
        # иначе он потеряется без следа.
        try:
            key = await panel_client.upsert_user(
                username=marzban_username,
                days=plan.days,
                traffic_gb=plan.traffic_gb,
                device_limit=device_limit_for(user),
            )
        except H1PanelError:
            logger.exception("Failed to issue paid key for tg_id=%s plan=%s", user.tg_id, plan.id)
            session.add(_payment(user, plan.id, sp, "paid_key_pending"))
            await session.commit()
            await message.answer(texts.MARZBAN_ERROR)
            return

        user.marzban_username = marzban_username
        subscription = await record_subscription(session, user.id, plan_id=plan.id, days=plan.days)
        carry_extra_devices(user, subscription.expires_at)
        session.add(_payment(user, plan.id, sp, "paid"))
        await session.commit()
        expires_at = subscription.expires_at

    await message.answer(
        texts.PAYMENT_SUCCESS.format(
            expires=expires_at.strftime("%d.%m.%Y"),
            key=key,
        ),
        reply_markup=back_to_menu(keep_message=True),
    )


async def _device_paid(message: Message, panel_client: H1PanelClient) -> None:
    sp = message.successful_payment

    async with get_session() as session:
        user = await get_or_create_user(session, message.from_user)
        subscription = await get_active_subscription(session, user.id)

        if subscription is None or user.marzban_username is None:
            # Подписка успела закончиться между счётом и оплатой — фиксируем
            # платёж, дальше вручную через поддержку
            logger.error("Device paid without active subscription, tg_id=%s", user.tg_id)
            session.add(_payment(user, "device", sp, "paid_device_no_subscription"))
            await session.commit()
            await message.answer(texts.MARZBAN_ERROR)
            return

        new_limit = add_extra_device(user, subscription.expires_at)
        try:
            await panel_client.set_device_limit(user.marzban_username, new_limit)
        except H1PanelError:
            logger.exception("Failed to raise device limit for tg_id=%s", user.tg_id)
            await session.rollback()
            async with get_session() as retry_session:
                retry_user = await get_or_create_user(retry_session, message.from_user)
                retry_session.add(_payment(retry_user, "device", sp, "paid_device_pending"))
                await retry_session.commit()
            await message.answer(texts.MARZBAN_ERROR)
            return

        session.add(_payment(user, "device", sp, "paid"))
        await session.commit()
        expires = subscription.expires_at.strftime("%d.%m.%Y")

    await message.answer(
        texts.DEVICE_ADDED.format(limit=new_limit, expires=expires),
        reply_markup=back_to_menu(keep_message=True),
    )


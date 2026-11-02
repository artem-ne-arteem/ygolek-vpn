import logging

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery

from bot import texts
from bot.db.models import Payment
from bot.db.repo import get_or_create_user, marzban_username_for, record_subscription
from bot.db.session import get_session
from bot.keyboards import back_to_menu
from bot.h1panel.client import H1PanelClient, H1PanelError
from bot.plans import get_plan

logger = logging.getLogger(__name__)
router = Router()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    plan_id = pre_checkout_query.invoice_payload.removeprefix("plan:")
    if get_plan(plan_id) is None:
        await pre_checkout_query.answer(ok=False, error_message="Тариф больше не доступен")
        return
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, panel_client: H1PanelClient) -> None:
    sp = message.successful_payment
    plan_id = sp.invoice_payload.removeprefix("plan:")
    plan = get_plan(plan_id)
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
            )
        except H1PanelError:
            logger.exception("Failed to issue paid key for tg_id=%s plan=%s", user.tg_id, plan.id)
            session.add(
                Payment(
                    user_id=user.id,
                    plan_id=plan.id,
                    provider="stars",
                    amount=sp.total_amount,
                    currency=sp.currency,
                    status="paid_key_pending",
                    telegram_charge_id=sp.telegram_payment_charge_id,
                )
            )
            await session.commit()
            await message.answer(texts.MARZBAN_ERROR)
            return

        user.marzban_username = marzban_username
        subscription = await record_subscription(session, user.id, plan_id=plan.id, days=plan.days)
        session.add(
            Payment(
                user_id=user.id,
                plan_id=plan.id,
                provider="stars",
                amount=sp.total_amount,
                currency=sp.currency,
                status="paid",
                telegram_charge_id=sp.telegram_payment_charge_id,
            )
        )
        await session.commit()
        expires_at = subscription.expires_at

    await message.answer(
        texts.PAYMENT_SUCCESS.format(
            expires=expires_at.strftime("%d.%m.%Y"),
            key=key,
        ),
        reply_markup=back_to_menu(keep_message=True),
    )

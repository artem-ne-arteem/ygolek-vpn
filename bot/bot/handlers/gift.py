"""Подписка в подарок: покупатель платит звёздами и получает одноразовую
ссылку t.me/<бот>?start=gift_<code>, друг открывает её — подписка у него."""

import datetime as dt
import html
import logging

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, LabeledPrice, Message, SuccessfulPayment

from bot import texts
from bot.capacity import current_load, can_buy
from bot.config import Config
from bot.db.models import Payment, User
from bot.db.repo import (
    create_gift,
    get_gift_for_update,
    get_or_create_user,
    marzban_username_for,
    record_subscription,
)
from bot.db.session import get_session
from bot.devices import carry_extra_devices, device_limit_for
from bot.h1panel.client import H1PanelClient, H1PanelError
from bot.keyboards import back_to_menu, gift_menu, gift_share_menu, key_menu
from bot.plans import DEVICE_LIMIT, get_plan
from bot.telegram_utils import safe_answer, show_screen

logger = logging.getLogger(__name__)
router = Router()

GIFT_PAYLOAD_PREFIX = "gift:"
GIFT_START_PREFIX = "gift_"


async def gift_purchase_error(config: Config, payload: str) -> str | None:
    """Проверка перед оплатой подарка (для pre_checkout_query)."""
    if get_plan(payload.removeprefix(GIFT_PAYLOAD_PREFIX)) is None:
        return "Тариф больше не доступен"
    async with get_session() as session:
        # подарок добавит на сервер нового человека — как новая подписка
        if (await current_load(session, config)).is_full:
            return texts.CAPACITY_FULL_SHORT
    return None


@router.callback_query(F.data == "gift:show")
async def show_gift(callback: CallbackQuery) -> None:
    await safe_answer(callback)
    await show_screen(callback, texts.GIFT_SCREEN.format(devices=DEVICE_LIMIT), gift_menu())


@router.callback_query(F.data.startswith("gift:buy:"))
async def buy_gift(callback: CallbackQuery, config: Config) -> None:
    plan = get_plan(callback.data.removeprefix("gift:buy:"))
    if plan is None:
        await safe_answer(callback, "Тариф не найден", show_alert=True)
        return

    async with get_session() as session:
        full = (await current_load(session, config)).is_full
    if full:
        await safe_answer(callback)
        await show_screen(callback, texts.CAPACITY_FULL, back_to_menu())
        return

    await safe_answer(callback)
    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=texts.GIFT_PAYMENT_TITLE.format(title=plan.title),
        description=texts.GIFT_PAYMENT_DESCRIPTION.format(title=plan.title, devices=DEVICE_LIMIT),
        payload=f"{GIFT_PAYLOAD_PREFIX}{plan.id}",
        provider_token="",  # для Stars всегда пустой
        currency="XTR",
        prices=[LabeledPrice(label=f"Подарок: {plan.title}", amount=plan.price_stars)],
    )


async def gift_paid(message: Message) -> None:
    """Вызывается из payment.successful_payment для payload gift:<plan>."""
    sp: SuccessfulPayment = message.successful_payment
    plan = get_plan(sp.invoice_payload.removeprefix(GIFT_PAYLOAD_PREFIX))
    if plan is None:
        logger.error("Gift paid for unknown plan, payload=%s", sp.invoice_payload)
        return

    async with get_session() as session:
        user = await get_or_create_user(session, message.from_user)
        gift = await create_gift(session, user.id, plan.id, plan.days)
        session.add(
            Payment(
                user_id=user.id,
                plan_id=f"gift:{plan.id}",
                provider="stars",
                amount=sp.total_amount,
                currency=sp.currency,
                status="paid",
                telegram_charge_id=sp.telegram_payment_charge_id,
            )
        )
        await session.commit()
        code = gift.code

    bot_username = (await message.bot.me()).username
    link = f"https://t.me/{bot_username}?start={GIFT_START_PREFIX}{code}"
    await message.answer(
        texts.GIFT_PAID.format(title=plan.title, link=link),
        reply_markup=gift_share_menu(link, texts.GIFT_SHARE_TEXT.format(title=plan.title)),
        disable_web_page_preview=True,
    )


@router.message(CommandStart(deep_link=True, magic=F.args.startswith(GIFT_START_PREFIX)))
async def redeem_gift(
    message: Message, command: CommandObject, config: Config, panel_client: H1PanelClient
) -> None:
    code = command.args.removeprefix(GIFT_START_PREFIX)

    async with get_session() as session:
        user = await get_or_create_user(session, message.from_user)
        gift = await get_gift_for_update(session, code)

        if gift is None:
            await session.commit()
            await message.answer(texts.GIFT_NOT_FOUND, reply_markup=back_to_menu())
            return
        if gift.redeemed_by_user_id is not None:
            await session.commit()
            await message.answer(texts.GIFT_ALREADY_USED, reply_markup=back_to_menu())
            return
        if not await can_buy(session, config, user, "plan"):
            await session.commit()
            await message.answer(texts.GIFT_CAPACITY_FULL, reply_markup=back_to_menu())
            return

        plan = get_plan(gift.plan_id)
        title = plan.title if plan else f"{gift.days} дн."
        marzban_username = user.marzban_username or marzban_username_for(user.tg_id)

        # Пока панель не выдала ключ, подарок не помечаем использованным —
        # при ошибке откатываемся, и ссылка остаётся рабочей
        try:
            key = await panel_client.upsert_user(
                username=marzban_username,
                days=gift.days,
                traffic_gb=plan.traffic_gb if plan else None,
                device_limit=device_limit_for(user),
            )
        except H1PanelError:
            logger.exception("Failed to redeem gift %s for tg_id=%s", gift.id, user.tg_id)
            await session.rollback()
            await message.answer(texts.MARZBAN_ERROR)
            return

        user.marzban_username = marzban_username
        subscription = await record_subscription(session, user.id, plan_id=f"gift:{gift.plan_id}", days=gift.days)
        carry_extra_devices(user, subscription.expires_at)
        gift.redeemed_by_user_id = user.id
        gift.redeemed_at = dt.datetime.utcnow()
        buyer_id = gift.buyer_user_id
        await session.commit()
        expires_at = subscription.expires_at

        buyer = await session.get(User, buyer_id)
        buyer_tg_id = buyer.tg_id if buyer else None

    await message.answer(
        texts.GIFT_REDEEMED.format(title=title, expires=expires_at.strftime("%d.%m.%Y"), key=key),
        reply_markup=key_menu(),
    )

    if buyer_tg_id and buyer_tg_id != message.from_user.id:
        who = f"@{message.from_user.username}" if message.from_user.username else html.escape(message.from_user.full_name)
        try:
            await message.bot.send_message(buyer_tg_id, texts.GIFT_REDEEMED_BUYER.format(who=who, title=title))
        except Exception:
            logger.info("Could not notify gift buyer tg_id=%s", buyer_tg_id)

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice

from bot import texts
from bot.capacity import can_buy
from bot.config import Config
from bot.db.repo import get_active_subscription, get_or_create_user
from bot.db.session import get_session
from bot.devices import device_limit_for
from bot.keyboards import back_to_menu, devices_menu, plans_menu
from bot.plans import EXTRA_DEVICE_PRICE_STARS, MAX_EXTRA_DEVICES
from bot.telegram_utils import safe_answer, show_screen

router = Router()

DEVICE_PAYLOAD = "device:1"


async def _device_state(callback: CallbackQuery, config: Config) -> tuple[str, object, bool]:
    """Текст экрана, клавиатура и можно ли сейчас докупить устройство."""
    async with get_session() as session:
        user = await get_or_create_user(session, callback.from_user)
        subscription = await get_active_subscription(session, user.id)
        allowed = await can_buy(session, config, user, "device")
        await session.commit()

    if subscription is None:
        return texts.DEVICES_NEED_SUB, plans_menu(), False

    limit = device_limit_for(user)
    if user.active_extra_devices() >= MAX_EXTRA_DEVICES:
        return texts.DEVICES_MAX.format(limit=limit), back_to_menu(), False
    if not allowed:
        return texts.CAPACITY_FULL, back_to_menu(), False

    text = texts.DEVICES_SCREEN.format(
        limit=limit,
        price=EXTRA_DEVICE_PRICE_STARS,
        expires=subscription.expires_at.strftime("%d.%m.%Y"),
    )
    return text, devices_menu(can_add=True), True


@router.callback_query(F.data == "devices:show")
async def show_devices(callback: CallbackQuery, config: Config) -> None:
    await safe_answer(callback)
    text, markup, _ = await _device_state(callback, config)
    await show_screen(callback, text, markup)


@router.callback_query(F.data == "devices:buy")
async def buy_device(callback: CallbackQuery, config: Config) -> None:
    text, markup, allowed = await _device_state(callback, config)
    if not allowed:
        await safe_answer(callback)
        await show_screen(callback, text, markup)
        return

    await safe_answer(callback)
    async with get_session() as session:
        user = await get_or_create_user(session, callback.from_user)
        subscription = await get_active_subscription(session, user.id)
        new_limit = device_limit_for(user) + 1
    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=texts.DEVICE_PAYMENT_TITLE,
        description=texts.DEVICE_PAYMENT_DESCRIPTION.format(
            expires=subscription.expires_at.strftime("%d.%m.%Y"), limit=new_limit
        ),
        payload=DEVICE_PAYLOAD,
        provider_token="",  # для Stars всегда пустой
        currency="XTR",
        prices=[LabeledPrice(label="+1 устройство", amount=EXTRA_DEVICE_PRICE_STARS)],
    )

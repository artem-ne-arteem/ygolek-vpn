from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.plans import PLANS, TRIAL_ENABLED

PRIVACY_POLICY_URL = "https://telegra.ph/Politika-konfidencialnosti-Ygolek-VPN-08-07"
TERMS_URL = "https://telegra.ph/Polzovatelskoe-soglashenie-Ygolek-VPN-08-07"
SUPPORT_URL = "https://t.me/ygolek_support"


def main_menu(has_subscription: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_subscription:
        builder.button(text="🔑 Мой ключ", callback_data="mykey:show")
        builder.button(text="💳 Продлить подписку", callback_data="plans:show")
    else:
        if TRIAL_ENABLED:
            builder.button(text="🎁 Пробный период", callback_data="trial:activate")
        builder.button(text="💳 Купить подписку", callback_data="plans:show")
    builder.button(text="📲 Как подключиться", callback_data="help:show")
    builder.button(text="📄 Документы", callback_data="legal:show")
    builder.button(text="🆘 Поддержка", url=SUPPORT_URL)
    # главные действия — по одной кнопке в ряд, «Документы» и «Поддержка» — рядом
    main_buttons = len(list(builder.buttons)) - 2
    builder.adjust(*([1] * main_buttons), 2)
    return builder.as_markup()


def plans_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in PLANS:
        builder.button(
            text=f"{plan.title} — {plan.price_stars} ⭐",
            callback_data=f"plan:select:{plan.id}",
        )
    builder.button(text="⬅️ Меню", callback_data="menu:show")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu(keep_message: bool = False) -> InlineKeyboardMarkup:
    """keep_message=True — для сообщений с ключом: меню откроется новым
    сообщением, а ключ останется в чате."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Меню", callback_data="menu:new" if keep_message else "menu:show")
    return builder.as_markup()


def key_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📲 Как подключиться", callback_data="help:show")
    builder.button(text="⬅️ Меню", callback_data="menu:show")
    builder.adjust(1)
    return builder.as_markup()


def renew_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Продлить подписку", callback_data="plans:show")
    builder.button(text="⬅️ Меню", callback_data="menu:new")
    builder.adjust(1)
    return builder.as_markup()


def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Выдать подписку", callback_data="admin:grant")
    builder.button(text="📊 Статистика", callback_data="admin:stats")
    builder.adjust(1)
    return builder.as_markup()


def admin_grant_days_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for title, days in (("7 дней", 7), ("1 месяц", 30), ("3 месяца", 90), ("1 год", 365)):
        builder.button(text=title, callback_data=f"admin:days:{days}")
    builder.button(text="❌ Отмена", callback_data="admin:cancel")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def admin_cancel_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="admin:cancel")
    return builder.as_markup()


def legal_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔒 Политика конфиденциальности", url=PRIVACY_POLICY_URL)
    builder.button(text="📜 Пользовательское соглашение", url=TERMS_URL)
    builder.button(text="⬅️ Меню", callback_data="menu:show")
    builder.adjust(1)
    return builder.as_markup()

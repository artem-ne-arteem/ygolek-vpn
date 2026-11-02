from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.plans import PLANS

PRIVACY_POLICY_URL = "https://telegra.ph/Politika-konfidencialnosti-Ygolek-VPN-08-07"
TERMS_URL = "https://telegra.ph/Polzovatelskoe-soglashenie-Ygolek-VPN-08-07"
SUPPORT_URL = "https://t.me/ygolek_support"


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Пробный период", callback_data="trial:activate")
    builder.button(text="💳 Тарифы", callback_data="plans:show")
    builder.button(text="🔑 Мой ключ", callback_data="mykey:show")
    builder.button(text="📄 Документы", callback_data="legal:show")
    builder.button(text="🆘 Поддержка", url=SUPPORT_URL)
    builder.adjust(1)
    return builder.as_markup()


def plans_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in PLANS:
        builder.button(
            text=f"{plan.title} — {plan.price_stars} ⭐",
            callback_data=f"plan:select:{plan.id}",
        )
    builder.button(text="⬅️ Назад", callback_data="menu:show")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Меню", callback_data="menu:show")
    return builder.as_markup()


def legal_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔒 Политика конфиденциальности", url=PRIVACY_POLICY_URL)
    builder.button(text="📜 Пользовательское соглашение", url=TERMS_URL)
    builder.button(text="⬅️ Меню", callback_data="menu:show")
    builder.adjust(1)
    return builder.as_markup()

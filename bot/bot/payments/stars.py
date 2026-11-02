from aiogram import Bot
from aiogram.types import LabeledPrice

from bot import texts
from bot.plans import Plan
from bot.payments.base import PaymentProvider


class StarsProvider(PaymentProvider):
    """Оплата через нативные Telegram Stars — не требует эквайринга."""

    name = "stars"

    async def send_invoice(self, bot: Bot, chat_id: int, plan: Plan) -> None:
        await bot.send_invoice(
            chat_id=chat_id,
            title=texts.PAYMENT_TITLE.format(title=plan.title),
            description=texts.PAYMENT_DESCRIPTION.format(
                title=plan.title,
                traffic=texts.traffic_label(plan.traffic_gb),
                days=plan.days,
            ),
            payload=f"plan:{plan.id}",
            provider_token="",  # для Stars всегда пустой
            currency="XTR",
            prices=[LabeledPrice(label=plan.title, amount=plan.price_stars)],
        )

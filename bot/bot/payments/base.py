from abc import ABC, abstractmethod

from aiogram import Bot

from bot.plans import Plan


class PaymentProvider(ABC):
    """Общий интерфейс способа оплаты.

    Чтобы добавить новый способ (например ЮKassa), реализуй send_invoice()
    и зарегистрируй провайдера в payments/__init__.py — хендлеры в
    handlers/payment.py менять не нужно.
    """

    name: str

    @abstractmethod
    async def send_invoice(self, bot: Bot, chat_id: int, plan: Plan) -> None:
        """Отправить пользователю счёт на оплату тарифа."""
        raise NotImplementedError

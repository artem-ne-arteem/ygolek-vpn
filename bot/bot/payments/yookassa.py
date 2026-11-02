from aiogram import Bot

from bot.plans import Plan
from bot.payments.base import PaymentProvider


class YooKassaProvider(PaymentProvider):
    """TODO: подключить, когда будет ИП/ООО и ключи ЮKassa.

    Реализация будет отличаться от Stars: нужен отдельный HTTP-вызов к API
    ЮKassa для создания платежа и confirmation_url, плюс приём вебхука об
    успешной оплате (понадобится HTTP-сервер рядом с ботом). Интерфейс
    PaymentProvider уже рассчитан на это — send_invoice() просто должен
    отправить пользователю сообщение со ссылкой на оплату вместо нативного
    Telegram-инвойса.
    """

    name = "yookassa"

    async def send_invoice(self, bot: Bot, chat_id: int, plan: Plan) -> None:
        raise NotImplementedError("ЮKassa пока не подключена")

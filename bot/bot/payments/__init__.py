from bot.payments.base import PaymentProvider
from bot.payments.stars import StarsProvider
from bot.payments.yookassa import YooKassaProvider

_PROVIDERS: dict[str, PaymentProvider] = {
    "stars": StarsProvider(),
    "yookassa": YooKassaProvider(),
}


def get_provider(name: str) -> PaymentProvider:
    provider = _PROVIDERS.get(name)
    if provider is None:
        raise ValueError(f"Неизвестный способ оплаты: {name}")
    return provider

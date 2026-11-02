"""Тарифная сетка. Меняешь тут — меняется и в боте, и в выдаче ключей."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    id: str
    title: str
    days: int
    traffic_gb: int | None  # None = безлимит
    price_stars: int  # цена в Telegram Stars


# Лимит устройств на подписку — один на все тарифы, подписки от админа и триал
DEVICE_LIMIT = 5

# Целевая цена — 150 ₽ в месяц; в Stars это примерно 100 ⭐ (курс Stars
# плавает и зависит от платформы покупателя — сверяй при смене цены)
PLANS: list[Plan] = [
    Plan(id="1m", title="1 месяц", days=30, traffic_gb=None, price_stars=100),
]

# Пробный период временно выключен — верни True, чтобы снова включить
TRIAL_ENABLED = False
TRIAL_DAYS = 3
TRIAL_TRAFFIC_GB = 5


def get_plan(plan_id: str) -> Plan | None:
    return next((p for p in PLANS if p.id == plan_id), None)

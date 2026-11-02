"""Тарифная сетка. Меняешь тут — меняется и в боте, и в выдаче ключей."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    id: str
    title: str
    days: int
    traffic_gb: int | None  # None = безлимит
    price_stars: int  # цена в Telegram Stars


PLANS: list[Plan] = [
    Plan(id="1m", title="1 месяц", days=30, traffic_gb=200, price_stars=150),
    Plan(id="3m", title="3 месяца", days=90, traffic_gb=600, price_stars=400),
    Plan(id="12m", title="12 месяцев", days=365, traffic_gb=None, price_stars=1400),
]

TRIAL_DAYS = 3
TRIAL_TRAFFIC_GB = 5


def get_plan(plan_id: str) -> Plan | None:
    return next((p for p in PLANS if p.id == plan_id), None)

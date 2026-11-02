"""Ограничение продаж по мощности сервера.

Скорость на человека = канал сервера ÷ число людей с действующей подпиской.
Если с ещё одним человеком она упадёт ниже порога — «мощности закончились»:
не продаём новые подписки, продление уже закончившихся и докупку устройств.
Продлить действующую подписку можно всегда — нагрузки это не добавляет.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import Config
from bot.db.models import User
from bot.db.repo import count_active_users, get_active_subscription


@dataclass(frozen=True)
class Load:
    active_users: int
    max_users: int
    speed_per_user_mbps: float  # если добавится ещё один человек

    @property
    def is_full(self) -> bool:
        return self.active_users >= self.max_users


async def current_load(session: AsyncSession, config: Config) -> Load:
    active = await count_active_users(session)
    max_users = config.server_capacity_mbps // max(config.min_speed_per_user_mbps, 1)
    return Load(
        active_users=active,
        max_users=max_users,
        speed_per_user_mbps=config.server_capacity_mbps / (active + 1),
    )


async def can_buy(session: AsyncSession, config: Config, user: User, purchase: str) -> bool:
    """purchase: "plan" — подписка/продление, "device" — +1 устройство."""
    if purchase == "plan" and await get_active_subscription(session, user.id) is not None:
        return True
    return not (await current_load(session, config)).is_full

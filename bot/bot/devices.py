"""Докупленные устройства: +1 к лимиту до конца текущей подписки."""

import datetime as dt

from bot.db.models import User
from bot.plans import DEVICE_LIMIT


def device_limit_for(user: User, now: dt.datetime | None = None) -> int:
    return DEVICE_LIMIT + user.active_extra_devices(now)


def carry_extra_devices(user: User, new_expires_at: dt.datetime) -> None:
    """После продления: докупленные устройства живут до нового срока.

    Если подписка успела закончиться, докупленные сгорели вместе с ней.
    """
    if user.active_extra_devices() > 0:
        user.extra_devices_until = new_expires_at
    else:
        user.extra_devices = 0
        user.extra_devices_until = None


def add_extra_device(user: User, subscription_expires_at: dt.datetime) -> int:
    """+1 устройство до конца подписки; возвращает новый общий лимит."""
    if user.active_extra_devices() == 0:
        user.extra_devices = 0
    user.extra_devices += 1
    user.extra_devices_until = subscription_expires_at
    return device_limit_for(user)

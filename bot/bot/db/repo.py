import datetime as dt

from aiogram.types import User as TgUser
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Payment, Subscription, User


def marzban_username_for(tg_id: int) -> str:
    return f"tg{tg_id}"


async def get_or_create_user(session: AsyncSession, tg_user: TgUser) -> User:
    result = await session.execute(select(User).where(User.tg_id == tg_user.id))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(tg_id=tg_user.id, username=tg_user.username)
    session.add(user)
    await session.flush()
    return user


async def get_or_create_user_by_tg_id(session: AsyncSession, tg_id: int) -> User:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(tg_id=tg_id)
    session.add(user)
    await session.flush()
    return user


async def find_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(
        select(User).where(func.lower(User.username) == username.lstrip("@").lower())
    )
    return result.scalars().first()


async def get_active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    result = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.expires_at.desc())
    )
    sub = result.scalars().first()
    if sub is None or sub.expires_at < dt.datetime.utcnow():
        return None
    return sub


async def record_subscription(session: AsyncSession, user_id: int, plan_id: str, days: int) -> Subscription:
    existing = await get_active_subscription(session, user_id)
    start = existing.expires_at if existing else dt.datetime.utcnow()
    expires_at = start + dt.timedelta(days=days)
    sub = Subscription(user_id=user_id, plan_id=plan_id, expires_at=expires_at)
    session.add(sub)
    await session.flush()
    return sub


async def get_subscriptions_expiring_soon(
    session: AsyncSession, within: dt.timedelta
) -> list[tuple[Subscription, User]]:
    now = dt.datetime.utcnow()
    result = await session.execute(
        select(Subscription, User)
        .join(User, User.id == Subscription.user_id)
        .where(
            Subscription.reminder_sent.is_(False),
            Subscription.expires_at > now,
            Subscription.expires_at <= now + within,
        )
    )
    return list(result.all())


async def get_stats(session: AsyncSession) -> dict:
    now = dt.datetime.utcnow()

    total_users = (await session.execute(select(func.count(User.id)))).scalar_one()

    active_subscriptions = (
        await session.execute(
            select(func.count(func.distinct(Subscription.user_id))).where(
                Subscription.expires_at > now
            )
        )
    ).scalar_one()

    stars_payments = (
        await session.execute(
            select(func.count(Payment.id)).where(Payment.provider == "stars", Payment.status == "paid")
        )
    ).scalar_one()

    stars_revenue = (
        await session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.provider == "stars", Payment.status == "paid"
            )
        )
    ).scalar_one()

    return {
        "total_users": total_users,
        "active_subscriptions": active_subscriptions,
        "stars_payments": stars_payments,
        "stars_revenue": stars_revenue,
    }

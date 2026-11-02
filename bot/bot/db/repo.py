import datetime as dt
import secrets

from aiogram.types import User as TgUser
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Gift, Payment, Subscription, User


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


async def get_latest_subscriptions_around(
    session: AsyncSession, before: dt.timedelta, after: dt.timedelta
) -> list[tuple[Subscription, User]]:
    """Последние подписки пользователей, которые кончаются в окне
    [сейчас - after, сейчас + before].

    Берём только самую позднюю подписку каждого пользователя: продление
    создаёт новую строку, и напоминать про старую (уже перекрытую) нельзя.
    """
    now = dt.datetime.utcnow()
    latest = (
        select(Subscription.user_id, func.max(Subscription.expires_at).label("expires_at"))
        .group_by(Subscription.user_id)
        .subquery()
    )
    result = await session.execute(
        select(Subscription, User)
        .join(latest, (latest.c.user_id == Subscription.user_id) & (latest.c.expires_at == Subscription.expires_at))
        .join(User, User.id == Subscription.user_id)
        .where(
            Subscription.expires_at > now - after,
            Subscription.expires_at <= now + before,
        )
    )
    return list(result.all())


async def create_gift(session: AsyncSession, buyer_user_id: int, plan_id: str, days: int) -> Gift:
    gift = Gift(code=secrets.token_urlsafe(9), plan_id=plan_id, days=days, buyer_user_id=buyer_user_id)
    session.add(gift)
    await session.flush()
    return gift


async def get_gift_for_update(session: AsyncSession, code: str) -> Gift | None:
    """С блокировкой строки — чтобы один подарок нельзя было активировать дважды
    двумя одновременными /start."""
    result = await session.execute(select(Gift).where(Gift.code == code).with_for_update())
    return result.scalar_one_or_none()


async def count_active_users(session: AsyncSession) -> int:
    """Сколько людей сейчас с действующей подпиской."""
    now = dt.datetime.utcnow()
    return (
        await session.execute(
            select(func.count(func.distinct(Subscription.user_id))).where(Subscription.expires_at > now)
        )
    ).scalar_one()


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

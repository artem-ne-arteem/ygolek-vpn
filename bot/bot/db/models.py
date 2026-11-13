import datetime as dt

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Boolean, Integer, false, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    marzban_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)
    # Докупленные устройства сверх DEVICE_LIMIT. Действуют до extra_devices_until —
    # это срок подписки на момент покупки, продление его сдвигает.
    extra_devices: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    extra_devices_until: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    def active_extra_devices(self, now: dt.datetime | None = None) -> int:
        now = now or dt.datetime.utcnow()
        if self.extra_devices_until is None or self.extra_devices_until <= now:
            return 0
        return self.extra_devices or 0


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plan_id: Mapped[str] = mapped_column(String(32))
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime)
    # reminder_sent — напоминание за сутки (историческое имя колонки, на него
    # завязан и сайт). Новые колонки с server_default, потому что сайт
    # вставляет подписки сырым SQL и про них не знает.
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_3d_sent: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    expired_notified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plan_id: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(32))  # "stars" | "yookassa"
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(24), default="pending")
    telegram_charge_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class AppLogin(Base):
    """Вход в приложение Ygolek VPN через бота.

    Приложение создаёт запрос на сайте (POST /api/app/login/start) и показывает
    ссылку t.me/<бот>?start=app_<code>. Пользователь подтверждает вход в боте —
    строка получает user_id. Приложение забирает токен (POST /api/app/login/poll)
    и дальше ходит с ним в /api/app/me. Сайт пишет в таблицу сырым SQL, поэтому
    у всех колонок со значениями по умолчанию есть server_default.
    """

    __tablename__ = "app_logins"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Публичная часть: попадает в ссылку на бота
    code: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    # sha256 от секрета, который знает только приложение (им оно забирает токен)
    secret_hash: Mapped[str] = mapped_column(String(64))
    device: Mapped[str] = mapped_column(String(64), default="", server_default="")
    # pending → approved (в боте) → issued (токен выдан) | denied | revoked
    status: Mapped[str] = mapped_column(String(16), default="pending", server_default="pending")
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    # sha256 от токена приложения
    token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


class Gift(Base):
    """Подписка, оплаченная в подарок: покупатель получает ссылку
    t.me/<бот>?start=gift_<code>, по ней друг активирует подписку один раз."""

    __tablename__ = "gifts"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    plan_id: Mapped[str] = mapped_column(String(32))
    days: Mapped[int] = mapped_column(Integer)
    buyer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    redeemed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    redeemed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class CardOrder(Base):
    """Оплата картой / СБП через Platega.

    Статусы: pending — ссылка на оплату выдана; paid — Platega подтвердила
    оплату (колбэк на сайте или проверка ботом); fulfilled — подписка выдана;
    canceled — оплата не прошла. Выдаёт подписку только бот (bot/card_orders.py).
    Заказы с сайта вставляет сайт сырым SQL — отсюда server_default.
    """

    __tablename__ = "card_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plan_id: Mapped[str] = mapped_column(String(32))
    amount_rub: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="pending", server_default="pending", index=True)
    transaction_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    source: Mapped[str] = mapped_column(String(16), default="bot", server_default="bot")
    fulfil_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, server_default=func.now())
    paid_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    fulfilled_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

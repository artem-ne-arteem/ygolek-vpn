import datetime as dt

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Boolean, Integer, false
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

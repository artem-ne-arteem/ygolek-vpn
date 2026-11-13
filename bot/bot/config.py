import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _int_list(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(part) for part in value.split(",") if part.strip()]


def _str_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


@dataclass(frozen=True)
class Config:
    bot_token: str
    database_url: str

    h1_panel_mock: bool
    h1_panel_url: str
    h1_panel_token: str
    h1_panel_inbound_ids: list[str]
    h1_panel_channels: list[str]

    platega_merchant_id: str
    platega_secret: str

    yookassa_shop_id: str
    yookassa_secret_key: str

    admin_ids: list[int]
    admin_usernames: list[str]

    webapp_url: str

    # Ограничение нагрузки: канал сервера ÷ активные подписки не должен
    # опускаться ниже min_speed_per_user_mbps, иначе продажи закрываются
    server_capacity_mbps: int
    min_speed_per_user_mbps: int


def load_config() -> Config:
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set — скопируй .env.example в .env и заполни его")

    return Config(
        bot_token=bot_token,
        database_url=os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./ygolek_vpn.db"),
        h1_panel_mock=_bool(os.environ.get("H1_PANEL_MOCK"), default=True),
        h1_panel_url=os.environ.get("H1_PANEL_URL", ""),
        h1_panel_token=os.environ.get("H1_PANEL_TOKEN", ""),
        h1_panel_inbound_ids=_str_list(os.environ.get("H1_PANEL_INBOUND_IDS")),
        h1_panel_channels=_str_list(os.environ.get("H1_PANEL_CHANNELS")),
        platega_merchant_id=os.environ.get("PLATEGA_MERCHANT_ID", "").strip(),
        platega_secret=os.environ.get("PLATEGA_SECRET", "").strip(),
        yookassa_shop_id=os.environ.get("YOOKASSA_SHOP_ID", ""),
        yookassa_secret_key=os.environ.get("YOOKASSA_SECRET_KEY", ""),
        admin_ids=_int_list(os.environ.get("ADMIN_IDS")),
        admin_usernames=[
            name.lstrip("@").lower()
            for name in _str_list(os.environ.get("ADMIN_USERNAMES", "fyave"))
        ],
        # Адрес мини-аппа; пустая строка — кнопки мини-аппа не показываются
        webapp_url=os.environ.get("WEBAPP_URL", "https://ygolek-vpn.online/app"),
        # Сейчас бот выдаёт ключи только на сервер из H1_PANEL_URL (500 Мбит/с)
        server_capacity_mbps=int(os.environ.get("SERVER_CAPACITY_MBPS") or 500),
        min_speed_per_user_mbps=int(os.environ.get("MIN_SPEED_PER_USER_MBPS") or 100),
    )

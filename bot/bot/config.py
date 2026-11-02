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
    h1_panel_device_limit: int

    yookassa_shop_id: str
    yookassa_secret_key: str

    admin_ids: list[int]


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
        h1_panel_device_limit=int(os.environ.get("H1_PANEL_DEVICE_LIMIT") or 0),
        yookassa_shop_id=os.environ.get("YOOKASSA_SHOP_ID", ""),
        yookassa_secret_key=os.environ.get("YOOKASSA_SECRET_KEY", ""),
        admin_ids=_int_list(os.environ.get("ADMIN_IDS")),
    )

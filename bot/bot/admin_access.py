from aiogram.types import User as TgUser

from bot.config import Config


def is_admin(tg_user: TgUser | None, config: Config) -> bool:
    if tg_user is None:
        return False
    if tg_user.id in config.admin_ids:
        return True
    return bool(tg_user.username) and tg_user.username.lower() in config.admin_usernames

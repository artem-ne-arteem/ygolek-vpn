WELCOME = (
    "👋 Привет! Это Ygolek VPN.\n\n"
    "Быстрый и стабильный VPN на протоколе VLESS — работает в Happ, "
    "v2rayNG, v2RayTun и других поддерживающих VLESS клиентах.\n\n"
    "Выбери, с чего начать 👇"
)

TRIAL_DISABLED = "Пробный период сейчас недоступен. Выбери тариф ниже 👇"

TRIAL_ALREADY_USED = "Пробный период уже был использован на этом аккаунте. Выбери тариф ниже 👇"

TRIAL_ISSUED = (
    "🎁 Пробный доступ на {days} дн. и {traffic} активирован!\n\n"
    "Твой ключ:\n<code>{key}</code>\n\n"
    "Как подключиться — см. /help"
)

PLANS_HEADER = "Выбери тариф:"

PLAN_BUTTON = "{title} — {price} ⭐"

PAYMENT_TITLE = "Ygolek VPN — {title}"
PAYMENT_DESCRIPTION = "Подписка на {title} ({traffic}, {days} дн.)"

PAYMENT_SUCCESS = (
    "✅ Оплата получена, подписка активна до {expires}.\n\n"
    "Твой ключ:\n<code>{key}</code>\n\n"
    "Как подключиться — см. /help"
)

MY_KEY_NOT_FOUND = "У тебя пока нет активной подписки. Нажми /start, чтобы выбрать тариф."

MY_KEY = "Твоя текущая подписка активна до {expires}.\n\nКлюч:\n<code>{key}</code>"

MARZBAN_ERROR = (
    "⚠️ Не получилось выдать ключ — сервер VPN сейчас недоступен.\n\n"
    "Мы уже видим проблему, попробуй ещё раз через пару минут. Если оплата "
    "прошла, а ключ не приходит — напиши в поддержку (@ygolek_support), ничего не потеряется."
)

REMINDER = (
    "⏰ Подписка заканчивается {expires} — не забудь продлить.\n\n"
    "Продлить: /menu → 💳 Тарифы"
)

STATS = (
    "📊 Статистика\n\n"
    "Пользователей: {total_users}\n"
    "Активных подписок: {active_subscriptions}\n"
    "Оплат (Stars): {stars_payments}\n"
    "Выручка (Stars): {stars_revenue} ⭐"
)

ADMIN_MENU = "🛠 Админ-панель"

ADMIN_GRANT_ASK_USER = (
    "Кому выдать подписку? Пришли Telegram ID (число) или @username.\n\n"
    "По @username найдутся только те, кто уже запускал бота. ID можно "
    "узнать у @userinfobot."
)

ADMIN_GRANT_USER_NOT_FOUND = (
    "Пользователь {query} не найден в базе — он ещё не запускал бота. "
    "Пришли его Telegram ID числом."
)

ADMIN_GRANT_ASK_DAYS = "Подписка для {who}. На сколько дней? Выбери ниже или пришли число."

ADMIN_GRANT_BAD_DAYS = "Пришли число дней от 1 до 3650."

ADMIN_GRANT_DONE = (
    "✅ Подписка для {who} выдана до {expires}.\n\n"
    "Ключ:\n<code>{key}</code>"
)

ADMIN_GRANT_NOT_NOTIFIED = (
    "\n\n⚠️ Не получилось отправить ключ пользователю (он не запускал бота "
    "или заблокировал его) — перешли ключ вручную."
)

ADMIN_GRANT_CANCELLED = "Выдача подписки отменена."

GIFT_ISSUED = (
    "🎁 Тебе выдана подписка Ygolek VPN до {expires}.\n\n"
    "Твой ключ:\n<code>{key}</code>\n\n"
    "Как подключиться — см. /help"
)

LEGAL = (
    "Оформляя подписку, ты соглашаешься с условиями "
    "ниже 👇"
)

HELP = (
    "<b>Как подключиться</b>\n\n"
    "1. Установи приложение:\n"
    "   • iOS/Android/macOS/Windows — <b>Happ</b>\n"
    "   • Android — <b>v2rayNG</b>\n"
    "   • iOS — <b>v2RayTun</b>\n"
    "2. Скопируй свой ключ (кнопка «Мой ключ» в боте).\n"
    "3. В приложении выбери «Добавить по ссылке / Import from clipboard» и вставь ключ.\n"
    "4. Нажми «Подключиться».\n\n"
    "Если что-то не работает — пиши в поддержку: @ygolek_support."
)


def traffic_label(traffic_gb: int | None) -> str:
    return "безлимит трафика" if traffic_gb is None else f"{traffic_gb} ГБ"

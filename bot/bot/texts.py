import datetime as dt

WELCOME = (
    "👋 Привет! Это Ygolek.\n\n"
    "Быстрое и стабильное подключение на протоколе VLESS — работает в Happ, "
    "v2rayNG, v2RayTun и других поддерживающих VLESS клиентах.\n\n"
    "{status}"
)

STATUS_ACTIVE = "✅ Подписка активна до <b>{expires}</b> — осталось {left}."
STATUS_NONE = "Подписки пока нет — выбери тариф 👇"

TRIAL_DISABLED = "Пробный период сейчас недоступен. Выбери тариф ниже 👇"

TRIAL_ALREADY_USED = "Пробный период уже был использован на этом аккаунте. Выбери тариф ниже 👇"

TRIAL_ISSUED = (
    "🎁 Пробный доступ на {days} дн. и {traffic} активирован!\n\n"
    "Твой ключ:\n<code>{key}</code>\n\n"
    "Как подключиться — см. /help"
)

PLANS_HEADER = (
    "💳 <b>Подписка</b>\n\n"
    "Безлимитный трафик, до {devices} устройств на одну подписку.\n\n"
    "{prices}\n\n"
    "Оплата банковской картой, через СБП или звёздами Telegram.\n"
    "Если подписка уже активна, новый срок добавится к текущему, ключ останется прежним."
)

PLAN_PRICE_LINE = "• {title} — <b>{rub} ₽</b> или {stars} ⭐"

PLAN_BUTTON_CARD = "💳 Оплатить картой / СБП — {price} ₽"
PLAN_BUTTON_STARS = "⭐ Оплатить звёздами — {price} ⭐"

CARD_PAYMENT_STUB = (
    "Оплата картой и СБП временно недоступна — мы её подключаем. "
    "Пока можно оплатить звёздами Telegram."
)

PAYMENT_TITLE = "Ygolek — {title}"
PAYMENT_DESCRIPTION = "Подписка на {title}: {traffic}, до {devices} устройств, {days} дн."

PAYMENT_SUCCESS = (
    "✅ Оплата получена, подписка активна до {expires}.\n\n"
    "Твой ключ:\n<code>{key}</code>\n\n"
    "Как подключиться — см. /help"
)

MY_KEY_NOT_FOUND = "У тебя пока нет активной подписки. Выбери тариф 👇"

MY_KEY = (
    "🔑 <b>Твой ключ</b>\n\n"
    "Подписка активна до <b>{expires}</b> — осталось {left}.\n"
    "Устройств: до {devices}.\n\n"
    "<code>{key}</code>\n\n"
    "Нажми на ключ, чтобы скопировать, и вставь его в Happ или v2rayNG."
)

MARZBAN_ERROR = (
    "⚠️ Не получилось выдать ключ — сервер сейчас недоступен.\n\n"
    "Мы уже видим проблему, попробуй ещё раз через пару минут. Если оплата "
    "прошла, а ключ не приходит — напиши в поддержку (@ygolek_support), ничего не потеряется."
)

REMINDER_3D = (
    "⏰ Подписка закончится через {left} — {expires}.\n\n"
    "Продли заранее, чтобы доступ не отключился. Новый срок добавится к текущему, "
    "ключ останется тем же."
)

REMINDER_1D = (
    "⏰ Подписка закончится меньше чем через сутки — {expires}.\n\n"
    "Продли сейчас, чтобы не остаться без доступа. Ключ менять не придётся."
)

SUBSCRIPTION_EXPIRED = (
    "⛔️ Подписка закончилась, доступ отключён.\n\n"
    "Продли — и тот же ключ снова заработает, ничего перенастраивать не нужно."
)

STATS = (
    "📊 Статистика\n\n"
    "Пользователей: {total_users}\n"
    "Активных подписок: {active_subscriptions}\n"
    "Оплат (Stars): {stars_payments}\n"
    "Выручка (Stars): {stars_revenue} ⭐"
)

STATS_LOAD = (
    "\n\n📶 Нагрузка: {active} из {max_users} мест "
    "(канал {capacity} Мбит/с, минимум {min_speed} Мбит/с на человека)"
    "{full}"
)

CAPACITY_FULL = (
    "😔 <b>Мощности временно закончились</b>\n\n"
    "Сейчас нельзя оформить новую подписку, продлить закончившуюся или добавить "
    "устройство — сервер загружен. Мы уже расширяемся, загляни чуть позже.\n\n"
    "Если подписка действует — её можно продлить как обычно.\n"
    "Вопросы — @ygolek_support"
)

CAPACITY_FULL_SHORT = "Мощности временно закончились — попробуй позже"

DEVICES_SCREEN = (
    "📱 <b>Устройства</b>\n\n"
    "Сейчас можно подключить до <b>{limit}</b> устройств одним ключом.\n\n"
    "Добавь ещё одно за {price} ⭐ — оно будет работать до конца подписки "
    "({expires}) и сохранится, если продлить подписку вовремя."
)

DEVICES_MAX = (
    "📱 <b>Устройства</b>\n\n"
    "Сейчас можно подключить до <b>{limit}</b> устройств — это максимум для одной подписки."
)

DEVICES_NEED_SUB = "Сначала оформи подписку — устройства добавляются к действующей подписке."

DEVICE_PAYMENT_TITLE = "Ygolek — +1 устройство"
DEVICE_PAYMENT_DESCRIPTION = "Ещё одно устройство к подписке до {expires}. Всего станет {limit}."

DEVICE_ADDED = (
    "✅ Устройство добавлено! Теперь тем же ключом можно подключить до {limit} устройств "
    "— до {expires}."
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
    "или остановил его) — перешли ключ вручную."
)

ADMIN_GRANT_CANCELLED = "Выдача подписки отменена."

GIFT_ISSUED = (
    "🎁 Тебе выдана подписка Ygolek до {expires}.\n\n"
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


def time_left_label(left: dt.timedelta) -> str:
    days = left.days
    if days < 1:
        return "меньше суток"
    if days % 10 == 1 and days % 100 != 11:
        word = "день"
    elif 2 <= days % 10 <= 4 and not 12 <= days % 100 <= 14:
        word = "дня"
    else:
        word = "дней"
    return f"{days} {word}"


def welcome(expires_at: dt.datetime | None) -> str:
    if expires_at is None:
        return WELCOME.format(status=STATUS_NONE)
    status = STATUS_ACTIVE.format(
        expires=expires_at.strftime("%d.%m.%Y"),
        left=time_left_label(expires_at - dt.datetime.utcnow()),
    )
    return WELCOME.format(status=status)


def traffic_label(traffic_gb: int | None) -> str:
    return "безлимит трафика" if traffic_gb is None else f"{traffic_gb} ГБ"


GIFT_SCREEN = (
    "🎁 <b>Подарить подписку</b>\n\n"
    "Оплати подписку для друга — пришлём ссылку-подарок. Друг откроет её, "
    "и подписка сразу активируется у него: безлимитный трафик, до {devices} устройств.\n\n"
    "Ссылка одноразовая и не сгорает — можно подарить заранее, к празднику."
)

GIFT_BUTTON = "🎁 {title} — {price} ⭐"

GIFT_PAYMENT_TITLE = "Ygolek — подарок на {title}"
GIFT_PAYMENT_DESCRIPTION = "Подписка в подарок другу: {title}, безлимитный трафик, до {devices} устройств."

GIFT_PAID = (
    "🎁 Подарок готов!\n\n"
    "Отправь другу эту ссылку — по ней он активирует подписку на {title}:\n"
    "{link}\n\n"
    "Ссылка сработает один раз. Когда друг её откроет, я тебе напишу."
)

GIFT_SHARE_TEXT = "Дарю тебе подписку Ygolek на {title} 🎁 Открой ссылку, чтобы активировать"

GIFT_REDEEMED = (
    "🎁 Тебе подарили подписку на {title}!\n\n"
    "Подписка активна до <b>{expires}</b>.\n\n"
    "Твой ключ:\n<code>{key}</code>\n\n"
    "Нажми на ключ, чтобы скопировать, и вставь его в Happ или v2rayNG."
)

GIFT_REDEEMED_BUYER = "🎉 {who} активировал твой подарок — подписку на {title}. Спасибо, что делишься Ygolek!"

GIFT_NOT_FOUND = "Такой ссылки-подарка нет. Проверь, что скопировал её целиком."

GIFT_ALREADY_USED = "Этот подарок уже активирован."

GIFT_CAPACITY_FULL = (
    "Сейчас сервер заполнен, и активировать подарок не получится. "
    "Ссылка не сгорит — попробуй открыть её ещё раз позже."
)


# --- Вход в приложение Ygolek VPN ---------------------------------------------

APP_LOGIN_CONFIRM = (
    "🔐 <b>Вход в приложение Ygolek VPN</b>\n\n"
    "Устройство: <b>{device}</b>\n\n"
    "Подтверди, если это ты входишь в приложение. Подписка сама появится в нём.\n"
    "Если ты ничего не открывал — нажми «Отмена»."
)

APP_LOGIN_DONE = (
    "✅ Готово! Приложение на устройстве «{device}» вошло в твой аккаунт.\n"
    "Вернись в приложение — подписка уже там."
)

APP_LOGIN_DENIED = "Вход отменён. Приложение не получило доступ к аккаунту."

APP_LOGIN_EXPIRED = (
    "Эта ссылка для входа устарела или уже использована. "
    "Нажми «Войти» в приложении ещё раз."
)


def bot_description() -> str:
    """«Что умеет этот бот?» — до 512 символов."""
    from bot.plans import DEVICE_LIMIT, PLANS

    plan = PLANS[0]
    return (
        "Ygolek — быстрое и стабильное подключение по протоколу VLESS.\n\n"
        "Здесь можно:\n"
        f"— оформить подписку: {plan.title} — {plan.price_rub} ₽ или {plan.price_stars} ⭐ "
        f"(безлимитный трафик, до {DEVICE_LIMIT} устройств)\n"
        "— получить ключ и подключиться за пару кликов\n"
        "— написать в поддержку, если что-то не работает\n\n"
        "Жми /start, чтобы начать."
    )


def bot_short_description() -> str:
    """Короткое описание в профиле бота — до 120 символов."""
    from bot.plans import DEVICE_LIMIT, PLANS

    plan = PLANS[0]
    return f"Подписка Ygolek: безлимитный трафик, до {DEVICE_LIMIT} устройств. {plan.price_rub} ₽ / {plan.title.removeprefix('1 ')}."

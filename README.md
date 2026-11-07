# Ygolek VPN

VPN-сервис: Telegram-бот с продажей подписок и сайт с личным кабинетом и
мини-приложением. Пользователи и ключи создаются через API панели H1
(h1cloud). Ключи открываются в **Happ** и **v2rayNG / v2RayTun**.

```
bot/     — Telegram-бот на aiogram (подписки, подарки, устройства, выдача ключей)
site/    — сайт на Next.js (тариф, FAQ, личный кабинет, мини-приложение)
legal/   — пользовательское соглашение и политика конфиденциальности
```

## Быстрый старт

### Бот

```bash
cd bot
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
# впиши BOT_TOKEN от @BotFather, остальное можно оставить как есть —
# H1_PANEL_MOCK=true выдаёт фейковые ключи, чтобы протестировать весь флоу
# без обращения к панели
python -m bot.main
```

В Telegram: `/start` → тариф → оплата Stars (в тестовом режиме Telegram сам
подставляет тестовые платежи) → бот присылает ключ.

Для работы с настоящей панелью в `bot/.env` нужны `H1_PANEL_MOCK=false`,
`H1_PANEL_URL` и `H1_PANEL_TOKEN` — см. комментарии в `bot/.env.example` и
[документацию API панели](https://my.h1cloud.net/api-docs#h1-panel-api).

### Сайт

```bash
cd site
npm install
copy .env.example .env.local
# впиши NEXT_PUBLIC_BOT_USERNAME — username бота без @
npm run dev
```

Открой http://localhost:3000 — сайт с тарифом, кнопки ведут в бота.

## Что дальше

- Подключение ЮKassa (`bot/bot/payments/yookassa.py` — заготовка интерфейса,
  сама интеграция и приём вебхуков ещё не реализованы).
- Несколько серверов и выбор ближайшего при выдаче ключа.

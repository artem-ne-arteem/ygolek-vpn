# Ygolek VPN

MVP-каркас VPN-сервиса: лендинг + Telegram-бот с продажей подписок + скрипт
поднятия VPN-ноды (VLESS+Reality через Marzban). Ключи, которые выдаёт бот,
открываются в **Happ** и **v2rayNG / v2RayTun**.

```
bot/     — Telegram-бот на aiogram (продажа тарифов, триал, выдача ключей)
site/    — лендинг на Next.js (тарифы, FAQ, кнопки в бота)
infra/   — установка VPN-ноды (Marzban/Xray) на VPS
```

## Быстрый старт

### Бот

```bash
cd bot
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
# впиши BOT_TOKEN от @BotFather, остальное можно оставить как есть —
# MARZBAN_MOCK=true выдаёт фейковые ключи, чтобы протестировать весь флоу
# без реального сервера
python -m bot.main
```

В Telegram: `/start` → пробный период / тарифы → оплата Stars (в тестовом
режиме Telegram сам подставляет тестовые платежи) → бот присылает ключ.

### Сайт

```bash
cd site
npm install
copy .env.example .env.local
# впиши NEXT_PUBLIC_BOT_USERNAME — username бота без @
npm run dev
```

Открой http://localhost:3000 — лендинг с тарифами, кнопки ведут в бота.

### VPN-нода

Когда готовы тестировать по-настоящему (не в mock-режиме) — см.
[`infra/README.md`](infra/README.md): аренда VPS → DNS → `setup-marzban.sh` →
переключение бота на `MARZBAN_MOCK=false`.

## Что дальше (не входит в эту итерацию)

- Подключение ЮKassa (`bot/bot/payments/yookassa.py` — заготовка интерфейса,
  сама интеграция и приём вебхуков ещё не реализованы).
- Несколько VPN-нод и выбор ближайшей при выдаче ключа.
- Автопродление / напоминания об истечении подписки.
- Реферальная программа.

# Pay Bot — крипто-оплата через Crypto Pay

Telegram-бот для приёма оплаты в криптовалюте (USDT и другие активы Crypto Pay).

## Возможности

- 💰 Выбор суммы: пресеты или своя сумма
- 🧾 Создание чека через Crypto Bot (одноразовая ссылка на оплату)
- 🔄 Автопроверка оплаты (поллинг каждые `PAYMENT_POLL_INTERVAL` сек)
- 🔔 Уведомления админу: «Новый чек» и «Чек оплачен»
- 🛠 Панель администратора: все чеки, фильтры по статусу, статистика,
  подтверждение и отмена чекова
- 📄 Пользователь видит свои чеки и статусы

## Запуск локально

1. `cp .env.example .env` и заполни токены (см. ниже).
2. `python -m venv .venv && .venv\Scripts\activate` (Windows) или `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python -m bot`

## Переменные окружения (`.env`)

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен от [@BotFather](https://t.me/BotFather) |
| `CRYPTO_PAY_TOKEN` | App Token от [@CryptoBot](https://t.me/CryptoBot) → Payments |
| `ADMIN_IDS` | ID администраторов через запятую |
| `ADMIN_USERNAME` | Ваш username (для ссылок на связь) |
| `AMOUNT_PRESETS` | Пресеты сумм через запятую (USDT) |
| `CRYPTO_ASSET` | Валюта чека (USDT, TON, BTC, TRX…) |
| `PAYMENT_POLL_INTERVAL` | Сек. между проверками оплат |
| `DATABASE_URL` | Пусто = SQLite (`data.db`), или PostgreSQL URL |
| `PORT` / `WEBHOOK_URL` / `WEBHOOK_SECRET` | Режим webhook (Render) |

## Деплой на Render

1. Новый **Web Service** → подключь репозиторий `nft-battle/pay-bot`
   (или Blueprint по `render.yaml`).
2. Задай секреты в Environment: `BOT_TOKEN`, `CRYPTO_PAY_TOKEN`, `ADMIN_IDS`,
   `DATABASE_URL` (опц.) — `ADMIN_USERNAME` при необходимости.
3. `WEBHOOK_URL` подставится автоматически из `RENDER_EXTERNAL_URL`.
4. Health check: `/health` (чтобы Render не вырубал бота).

Проверка: `https://<app>.onrender.com/health` → `{"ok": true}`.
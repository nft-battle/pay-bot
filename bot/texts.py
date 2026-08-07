WELCOME_TEXT = (
    "👋 <b>Добро пожаловать!</b>\n\n"
    "Здесь вы можете оплатить услуги через криптовалюту (Crypto Pay).\n"
    "Выберите сумму, получите чек на оплату — и после оплаты вам придут квитанции.\n\n"
    "💰 Оплата принимается через <b>Crypto Bot</b> — безопасно и мгновенно."
)

CHOOSE_AMOUNT_TEXT = "💰 <b>Выберите сумму пополнения:</b>"

CUSTOM_AMOUNT_PROMPT = (
    "✏️ Введите свою сумму в <b>USDT</b> (число, например: 12.5)\n"
    "Минимум: <b>{min_amt}</b>, максимум: <b>{max_amt}</b>"
)

BAD_AMOUNT = "⚠️ Неверная сумма. Введите число (например: 12.5)"

CHECK_CREATED = (
    "🧾 <b>Чек #{payment_id} создан!</b>\n\n"
    "💵 Сумма: <b>{amount}</b>\n"
    "🕒 Время создания: <code>{created}</code>\n\n"
    "Нажмите <b>«Оплатить»</b>, чтобы перейти к оплате через Crypto Bot.\n"
    "После оплаты чек будет автоматически подтверждён."
)

CHECK_PENDING = "⏳ Чек #{payment_id} ещё не оплачен. Откройте платёж и завершите оплату."

CHECK_PAID_USER = "✅ Чек #{payment_id} <b>оплачен</b>! Ожидайте подтверждения администратором."

CHECK_NOT_FOUND = "❌ Чек не найден."

CHECK_CANCELLED = "🚫 Чек #{payment_id} отменён."

CANCELLED_OK = "✅ Чек отменён."

NOT_ADMIN = "⛔ Нет доступа. Вы не администратор."

ADMIN_PANEL_TEXT = "🛠 <b>Панель администратора</b>"

ADMIN_EMPTY = "📭 Список пуст."

STATS_TEXT = (
    "📊 <b>Статистика</b>\n\n"
    "💰 Оплачено: <b>{paid_amount} USDT</b>\n"
    "🧾 Всего чеков: <b>{total}</b>\n"
    "⏳ Неоплаченных: <b>{pending}</b>\n"
    "✅ Оплаченных: <b>{paid}</b>\n"
    "🚀 Подтверждённых: <b>{confirmed}</b>\n"
    "❌ Отменённых: <b>{cancelled}</b>\n"
    "👥 Уникальных пользователей: <b>{users}</b>"
)

PAY_DETAILS_TEXT = (
    "🧾 <b>Чек #{payment_id}</b>\n\n"
    "💵 Сумма: <b>{amount}</b>\n"
    "👤 Отправитель: {user_ref}\n"
    "📊 Статус: <b>{status}</b>\n"
    "🕒 Создан: <code>{created}</code>\n"
    "✅ Оплачен: <code>{paid}</code>"
)

ADMIN_DETAILS_TEXT = (
    "🧾 <b>Чек #{payment_id}</b>\n\n"
    "💵 Сумма: <b>{amount}</b>\n"
    "👤 Пользователь: {user_ref}\n"
    "📊 Статус: <b>{status}</b>\n"
    "🕒 Создан: <code>{created}</code>\n"
    "✅ Оплачен: <code>{paid}</code>"
)

CONFIRMED_ADMIN = "🚀 Чек #{payment_id} подтверждён."

CONFIRMED_USER = (
    "🚀 <b>Чек #{payment_id} подтверждён!</b>\n"
    "Оплата прошла успешно. Спасибо за доверие!"
)

CANCELLED_ADMIN = "❌ Чек #{payment_id} отменён."
CANCELLED_USER = "❌ Чек #{payment_id} был отменён администратором."

PAYMENT_EXPIRED = "⏰ Срок действия чека истёк."
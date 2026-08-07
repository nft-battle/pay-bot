from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

STATUS_LABELS = {
    "pending": "⏳ Ожидает оплаты",
    "paid": "✅ Оплачен",
    "confirmed": "🚀 Подтверждён",
    "cancelled": "❌ Отменён",
}

PAGE_SIZE = 10


class PayCB(CallbackData, prefix="pay"):
    action: str
    amount: float = 0
    payment_id: int = 0
    page: int = 0


class AdminCB(CallbackData, prefix="adm"):
    action: str
    payment_id: int = 0
    page: int = 0
    status: str = ""


def main_menu_kb() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="🛒 Оплатить", callback_data=PayCB(action="pay").pack())],
        [InlineKeyboardButton(text="📄 Мои чеки", callback_data=PayCB(action="my").pack())],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def inline_pay_kb(pay_url: str, payment_id: int) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="💳 Оплатить", url=pay_url)],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=PayCB(action="check", payment_id=payment_id).pack())],
        [InlineKeyboardButton(text="🚫 Отменить чек", callback_data=PayCB(action="cancel_check", payment_id=payment_id).pack())],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def my_checks_kb(payments: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    kb = []
    for p in payments:
        kb.append(
            [
                InlineKeyboardButton(
                    text=f"#{p['id']} · {p['amount']:g} {p['asset']} · {STATUS_LABELS.get(p['status'], p['status'])}",
                    callback_data=PayCB(action="pay_details", payment_id=p["id"]).pack(),
                )
            ]
        )
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=PayCB(action="my", page=page - 1).pack()))
    nav.append(InlineKeyboardButton(text="🏠 Главное", callback_data=PayCB(action="back_main").pack()))
    if len(payments) == 20:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=PayCB(action="my", page=page + 1).pack()))
    kb.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_panel_kb() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="🧾 Все чеки", callback_data=AdminCB(action="all").pack())],
        [InlineKeyboardButton(text="⏳ Неоплаченные", callback_data=AdminCB(action="list", status="pending").pack())],
        [InlineKeyboardButton(text="✅ Оплаченные", callback_data=AdminCB(action="list", status="paid").pack())],
        [InlineKeyboardButton(text="🚀 Подтверждённые", callback_data=AdminCB(action="list", status="confirmed").pack())],
        [InlineKeyboardButton(text="❌ Отменённые", callback_data=AdminCB(action="list", status="cancelled").pack())],
        [InlineKeyboardButton(text="📊 Статистика", callback_data=AdminCB(action="stats").pack())],
        [InlineKeyboardButton(text="🏠 Главное", callback_data=PayCB(action="back_main").pack())],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_list_kb(payments: list[dict], page: int = 0, status: str = "") -> InlineKeyboardMarkup:
    kb = []
    for p in payments:
        kb.append(
            [
                InlineKeyboardButton(
                    text=f"#{p['id']} · {p['amount']:g} {p['asset']} · {STATUS_LABELS.get(p['status'], p['status'])}",
                    callback_data=AdminCB(action="details", payment_id=p["id"]).pack(),
                )
            ]
        )
    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=AdminCB(action="prev", page=page - 1, status=status).pack()
            )
        )
    nav.append(InlineKeyboardButton(text="🔙 Панель", callback_data=AdminCB(action="panel").pack()))
    if len(payments) == PAGE_SIZE:
        nav.append(
            InlineKeyboardButton(
                text="➡️", callback_data=AdminCB(action="next", page=page + 1, status=status).pack()
            )
        )
    kb.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_details_kb(payment_id: int, status: str) -> InlineKeyboardMarkup:
    kb = []
    if status == "paid":
        kb.append([InlineKeyboardButton(text="🚀 Подтвердить", callback_data=AdminCB(action="confirm", payment_id=payment_id).pack())])
    if status in ("pending", "paid"):
        kb.append([InlineKeyboardButton(text="❌ Отменить", callback_data=AdminCB(action="cancel", payment_id=payment_id).pack())])
    kb.append([InlineKeyboardButton(text="⬅️", callback_data=AdminCB(action="panel").pack())])
    return InlineKeyboardMarkup(inline_keyboard=kb)
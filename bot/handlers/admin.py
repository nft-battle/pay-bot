import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ..config import ADMIN_IDS
from ..database import db
from ..keyboards import (
    AdminCB,
    STATUS_LABELS,
    admin_details_kb,
    admin_list_kb,
    admin_panel_kb,
)
from ..services.crypto_pay import CryptoPayError, crypto_pay
from ..texts import ADMIN_EMPTY, ADMIN_PANEL_TEXT, NOT_ADMIN, STATS_TEXT
from ..utils import esc, fmt_money, user_ref

logger = logging.getLogger(__name__)
router = Router()

PAGE_SIZE = 10


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _fmt_details(pay: dict) -> str:
    return (
        f"🧾 <b>Чек #{pay['id']}</b>\n\n"
        f"💵 Сумма: <b>{fmt_money(pay['amount'], pay.get('asset') or 'USDT')}</b>\n"
        f"👤 Пользователь: {user_ref(pay.get('username') or '', pay['user_id'])}\n"
        f"📊 Статус: <b>{STATUS_LABELS.get(pay['status'], pay['status'])}</b>\n"
        f"🕒 Создан: <code>{esc(pay.get('created_at') or '—')}</code>\n"
        f"✅ Оплачен: <code>{esc(pay.get('paid_at') or '—')}</code>\n"
        f"🔗 Инвойс: <code>{esc(pay.get('invoice_id') or '—')}</code>"
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer(NOT_ADMIN)
        return
    await message.answer(ADMIN_PANEL_TEXT, reply_markup=admin_panel_kb())


@router.callback_query(AdminCB.filter(F.action == "panel"))
async def adm_panel_cb(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(ADMIN_PANEL_TEXT, reply_markup=admin_panel_kb())
    await callback.answer()


async def _show_list(callback: CallbackQuery, status: str | None, page: int) -> None:
    payments = await db.list_payments(status=status, limit=PAGE_SIZE * (page + 2))
    payments = payments[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    if not payments:
        await callback.message.edit_text(ADMIN_EMPTY, reply_markup=admin_panel_kb())
        await callback.answer()
        return
    await callback.message.edit_text(
        "📋 <b>Список чеков</b>", reply_markup=admin_list_kb(payments, page=page, status=status or "")
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action.in_({"all", "list", "next", "prev"})))
async def adm_list(callback: CallbackQuery, query_data: AdminCB) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await _show_list(callback, query_data.status or None, query_data.page)


@router.callback_query(AdminCB.filter(F.action == "details"))
async def adm_details(callback: CallbackQuery, query_data: AdminCB) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    pay = await db.get_payment(query_data.payment_id)
    if not pay:
        await callback.message.edit_text("❌ Чек не найден.", reply_markup=admin_panel_kb())
        await callback.answer()
        return
    await callback.message.edit_text(
        _fmt_details(pay),
        reply_markup=admin_details_kb(pay["id"], pay["status"]),
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "confirm"))
async def adm_confirm(callback: CallbackQuery, query_data: AdminCB) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    pay = await db.get_payment(query_data.payment_id)
    if not pay or pay["status"] != "paid":
        await callback.message.edit_text(
            "❌ Чек недоступен для подтверждения.", reply_markup=admin_panel_kb()
        )
        await callback.answer()
        return
    await db.set_status(pay["id"], "confirmed")
    try:
        await callback.bot.send_message(
            pay["user_id"],
            f"🚀 Чек #{pay['id']} подтверждён. Оплата прошла успешно, спасибо!",
        )
    except Exception:
        logger.exception("Не удалось уведомить клиента %s", pay["user_id"])
    await callback.message.edit_text(
        f"🚀 Чек #{pay['id']} подтверждён.", reply_markup=admin_panel_kb()
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "cancel"))
async def adm_cancel(callback: CallbackQuery, query_data: AdminCB) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    pay = await db.get_payment(query_data.payment_id)
    if not pay or pay["status"] not in ("pending", "paid"):
        await callback.message.edit_text(
            "❌ Чек недоступен для отмены.", reply_markup=admin_panel_kb()
        )
        await callback.answer()
        return
    if pay.get("invoice_id"):
        try:
            await crypto_pay.delete_invoice(pay["invoice_id"])
        except CryptoPayError:
            logger.exception("Не удалось удалить инвойс")
    await db.set_status(pay["id"], "cancelled")
    try:
        await callback.bot.send_message(
            pay["user_id"], f"❌ Чек #{pay['id']} был отменён администратором."
        )
    except Exception:
        logger.exception("Не удалось уведомить клиента %s", pay["user_id"])
    await callback.message.edit_text(
        f"❌ Чек #{pay['id']} отменён.", reply_markup=admin_panel_kb()
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "stats"))
async def adm_stats(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    by_status = await db.count_by_status()
    total = sum(by_status.values())
    paid_amount = await db.total_amount_paid()
    users = await db.users_count()
    await callback.message.edit_text(
        STATS_TEXT.format(
            paid_amount=f"{paid_amount:,.2f}",
            total=total,
            pending=by_status.get("pending", 0),
            paid=by_status.get("paid", 0),
            confirmed=by_status.get("confirmed", 0),
            cancelled=by_status.get("cancelled", 0),
            users=users,
        ),
        reply_markup=admin_panel_kb(),
    )
    await callback.answer()
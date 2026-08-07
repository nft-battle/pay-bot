import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from ..config import AMOUNT_PRESETS, CRYPTO_ASSET, MAX_AMOUNT, MIN_AMOUNT
from ..database import db
from ..keyboards import (
    PayCB,
    amount_kb,
    inline_pay_kb,
    main_menu_kb,
    my_checks_kb,
)
from ..services.crypto_pay import CryptoPayError, crypto_pay
from ..services.notifications import notify_new_check
from ..texts import (
    BAD_AMOUNT,
    CHECK_CANCELLED,
    CHECK_CREATED,
    CHECK_NOT_FOUND,
    CHECK_PAID_USER,
    CHECK_PENDING,
    CHOOSE_AMOUNT_TEXT,
    CUSTOM_AMOUNT_PROMPT,
    PAYMENT_EXPIRED,
    WELCOME_TEXT,
)
from ..utils import esc, fmt_money

logger = logging.getLogger(__name__)
router = Router()


class CustomFSM(StatesGroup):
    amount = State()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu_kb())


@router.callback_query(PayCB.filter(F.action == "back_main"))
async def cb_back_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(PayCB.filter(F.action == "pay"))
async def cb_pay(callback: CallbackQuery) -> None:
    await callback.message.edit_text(CHOOSE_AMOUNT_TEXT, reply_markup=amount_kb())
    await callback.answer()


@router.callback_query(PayCB.filter(F.action == "custom"))
async def cb_custom(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CustomFSM.amount)
    await callback.message.edit_text(
        CUSTOM_AMOUNT_PROMPT.format(min_amt=MIN_AMOUNT, max_amt=MAX_AMOUNT)
    )
    await callback.answer()


@router.message(CustomFSM.amount)
async def got_custom_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = float((message.text or "").replace(",", ".").strip())
    except ValueError:
        amount = 0.0
    if not (MIN_AMOUNT <= amount <= MAX_AMOUNT):
        await message.answer(BAD_AMOUNT)
        return
    await state.clear()
    await _start_payment(message, amount)


@router.callback_query(PayCB.filter(F.action == "amount"))
async def cb_amount(callback: CallbackQuery, callback_data: PayCB) -> None:
    await callback.message.edit_text(CHOOSE_AMOUNT_TEXT, reply_markup=amount_kb())
    await callback.answer()
    await _start_payment(callback.message, callback_data.amount, from_callback=True)


async def _start_payment(message, amount: float, from_callback: bool = False) -> None:
    user = message.from_user
    pay_id = await db.create_payment(user.id, user.username or "", amount, CRYPTO_ASSET)
    pay = await db.get_payment(pay_id)
    desc = f"Платёж #{pay_id:04d} — {fmt_money(amount, CRYPTO_ASSET)}"
    try:
        invoice = await crypto_pay.create_invoice(CRYPTO_ASSET, amount, desc)
    except CryptoPayError as exc:
        logger.exception("Ошибка создания инвойса")
        if from_callback:
            await message.answer(f"❌ Не удалось создать чек: {esc(exc)}")
        else:
            await message.answer(f"❌ Не удалось создать чек: {esc(exc)}")
        return
    await db.set_invoice(
        pay_id, int(invoice["invoice_id"]), invoice["pay_url"], invoice.get("pay_url", "")
    )
    pay = await db.get_payment(pay_id)
    await notify_new_check(message.bot, pay)
    text = CHECK_CREATED.format(
        payment_id=pay_id,
        amount=fmt_money(amount, CRYPTO_ASSET),
        created=esc(pay.get("created_at") or ""),
    )
    await message.answer(text, reply_markup=inline_pay_kb(invoice["pay_url"], pay_id))


@router.callback_query(PayCB.filter(F.action == "check"))
async def cb_check(callback: CallbackQuery, query_data: PayCB) -> None:
    pay = await db.get_payment(query_data.payment_id)
    if not pay:
        await callback.message.edit_text(CHECK_NOT_FOUND)
        await callback.answer()
        return
    if pay["status"] == "pending":
        await callback.message.edit_text(
            CHECK_PENDING.format(payment_id=pay["id"]),
            reply_markup=inline_pay_kb(pay["pay_url"] or "", pay["id"]),
        )
        await callback.answer()
        return
    if pay["status"] == "paid":
        await callback.message.edit_text(CHECK_PAID_USER.format(payment_id=pay["id"]))
        await callback.answer()
        return
    await callback.message.edit_text(PAYMENT_EXPIRED)
    await callback.answer()


@router.callback_query(PayCB.filter(F.action == "cancel_check"))
async def cb_cancel_check(callback: CallbackQuery, query_data: PayCB) -> None:
    pay = await db.get_payment(query_data.payment_id)
    if not pay:
        await callback.message.edit_text(CHECK_NOT_FOUND)
        await callback.answer()
        return
    if pay["status"] == "pending":
        if pay.get("invoice_id"):
            try:
                await crypto_pay.delete_invoice(pay["invoice_id"])
            except CryptoPayError:
                logger.exception("Не удалось удалить инвойс")
        await db.set_status(pay["id"], "cancelled")
    await callback.message.edit_text(CHECK_CANCELLED.format(payment_id=pay["id"]))
    await callback.answer()


@router.callback_query(PayCB.filter(F.action == "my"))
async def cb_my(callback: CallbackQuery, query_data: PayCB) -> None:
    offset = query_data.page * 20
    payments = await db.list_payments_by_user(callback.from_user.id, limit=21)
    payments = payments[offset : offset + 20]
    if not payments:
        await callback.message.edit_text(
            "У вас нет чеков.", reply_markup=main_menu_kb()
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        "📄 <b>Ваши чеки:</b>",
        reply_markup=my_checks_kb(payments, page=query_data.page),
    )
    await callback.answer()


@router.callback_query(PayCB.filter(F.action == "pay_details"))
async def cb_pay_details(callback: CallbackQuery, query_data: PayCB) -> None:
    pay = await db.get_payment(query_data.payment_id)
    if not pay:
        await callback.message.edit_text(CHECK_NOT_FOUND)
        await callback.answer()
        return
    from ..keyboards import STATUS_LABELS

    status = STATUS_LABELS.get(pay["status"], pay["status"])
    text = (
        f"🧾 <b>Чек #{pay['id']}</b>\n\n"
        f"💵 Сумма: <b>{fmt_money(pay['amount'])}</b>\n"
        f"📊 Статус: <b>{status}</b>\n"
        f"🕒 Создан: <code>{esc(pay.get('created_at') or '—')}</code>\n"
        f"✅ Оплачен: <code>{esc(pay.get('paid_at') or '—')}</code>"
    )
    await callback.message.edit_text(text, reply_markup=main_menu_kb())
    await callback.answer()


@router.message(F.text)
async def fallback(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())
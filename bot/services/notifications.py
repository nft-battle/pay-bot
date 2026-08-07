import logging

from aiogram import Bot

from ..config import ADMIN_IDS
from ..utils import esc, fmt_money, user_ref

logger = logging.getLogger(__name__)


def format_payment(pay: dict) -> str:
    return (
        f"💎 Чек #{pay['id']}\n"
        f"👤 {user_ref(pay.get('username') or '', pay['user_id'])} (ID: <code>{pay['user_id']}</code>)\n"
        f"💵 Сумма: <b>{fmt_money(pay['amount'], pay.get('asset') or 'USDT')}</b>\n"
        f"🕒 Создан: <code>{esc(pay.get('created_at') or '—')}</code>\n"
        f"✅ Оплачен: <code>{esc(pay.get('paid_at') or '—')}</code>\n"
    )


async def notify_admins(bot: Bot, text: str, **kwargs) -> None:
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, **kwargs)
        except Exception:
            logger.exception("Не удалось отправить админу %s", admin_id)


async def notify_new_check(bot: Bot, pay: dict) -> None:
    text = "🆕 <b>Новый чек</b>\n" + format_payment(pay) + "\n💌 Ожидает оплаты."
    await notify_admins(bot, text)


async def notify_paid(bot: Bot, pay: dict) -> None:
    text = "✅ <b>Чек оплачен</b>\n" + format_payment(pay) + "\n🔔 Проверьте перевод."
    await notify_admins(bot, text)


async def client_paid(bot: Bot, pay: dict) -> None:
    await bot.send_message(
        pay["user_id"],
        f"✅ Оплата чека #{pay['id']} на {fmt_money(pay['amount'])} подтверждена. Спасибо!",
    )
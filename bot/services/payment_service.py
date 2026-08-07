import asyncio
import logging

from aiogram import Bot

from ..database import db
from ..utils import esc
from .crypto_pay import crypto_pay
from .notifications import client_paid, notify_paid

logger = logging.getLogger(__name__)


class PaymentPoller:
    """Периодически сверяет инвойсы Crypto Pay с неоплаченными чеками."""

    def __init__(self, bot: Bot, interval: int = 10):
        self.bot = bot
        self.interval = interval

    async def run(self) -> None:
        while True:
            try:
                await self.check_paid()
            except Exception:
                logger.exception("Ошибка при проверке оплат")
            await asyncio.sleep(self.interval)

    async def check_paid(self) -> None:
        if not crypto_pay.token:
            return
        pending = [p for p in await db.list_payments(status="pending") if p.get("invoice_id")]
        if not pending:
            return
        paid_ids: set[int] = set()
        try:
            invoices = await crypto_pay.get_paid_invoices()
        except Exception:
            logger.exception("Не удалось получить оплаченные инвойсы")
            return
        for inv in invoices:
            inv_id = inv.get("invoice_id")
            if inv_id:
                paid_ids.add(int(inv_id))
        for pay in pending:
            if pay["invoice_id"] not in paid_ids:
                continue
            fresh = await db.get_payment(pay["id"])
            if not fresh or fresh["status"] != "pending":
                continue
            await db.mark_paid(pay["id"])
            logger.info("Чек №%s оплачен", pay["id"])
            await client_paid(self.bot, fresh)
            await notify_paid(self.bot, fresh)
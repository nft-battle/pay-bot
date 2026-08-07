import logging

import aiohttp

from ..config import CRYPTO_PAY_TOKEN

logger = logging.getLogger(__name__)

API_BASE = "https://pay.crypt.bot/api"


class CryptoPayError(Exception):
    pass


class CryptoPay:
    """Клиент Crypto Pay API (https://help.crypt.bot/crypto-pay-api)."""

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Crypto-Pay-API-Token": token,
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, **params) -> dict:
        if not self.token:
            raise CryptoPayError("CRYPTO_PAY_TOKEN не задан")
        url = f"{API_BASE}/{method}"
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.post(url, headers=self.headers, json=params) as resp:
                data = await resp.json(content_type=None)
        if not data.get("ok"):
            raise CryptoPayError(str(data.get("error", {}).get("message", "unknown error")))
        return data["result"]

    async def create_invoice(
        self, asset: str, amount: float, description: str
    ) -> dict:
        return await self._request(
            "createInvoice",
            asset=asset,
            amount=amount,
            description=description[:500],
            allow_anonymous=True,
            allow_comments=True,
            allow_repeated_payment=False,
        )

    async def check_invoice(self, invoice_id: int) -> dict | None:
        result = await self._request("getInvoices", invoice_ids=str(invoice_id))
        items = result.get("items", []) if isinstance(result, dict) else (result or [])
        return items[0] if items else None

    async def get_paid_invoices(self) -> list[dict]:
        result = await self._request("getInvoices", status="paid")
        if isinstance(result, dict):
            return result.get("items", [])
        return result or []

    async def delete_invoice(self, invoice_id: int) -> None:
        await self._request("deleteInvoice", invoice_id=invoice_id)

    async def get_balance(self) -> list[dict]:
        return await self._request("getBalance")


crypto_pay = CryptoPay(CRYPTO_PAY_TOKEN)
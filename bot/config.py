import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
CRYPTO_PAY_TOKEN: str = os.getenv("CRYPTO_PAY_TOKEN", "").strip()

ADMIN_IDS: list[int] = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
]
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "").strip().lstrip("@")

AMOUNT_PRESETS: list[int] = [
    int(x)
    for x in os.getenv("AMOUNT_PRESETS", "5,10,25,50,100,250,500").split(",")
    if x.strip().isdigit()
]
CRYPTO_ASSET: str = os.getenv("CRYPTO_ASSET", "USDT").strip() or "USDT"

PAYMENT_POLL_INTERVAL: int = max(3, int(os.getenv("PAYMENT_POLL_INTERVAL", "10")))

DB_PATH: str = os.getenv("DB_PATH", "data.db").strip()
DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()

PORT: int = int(os.getenv("PORT", "8080"))
WEBHOOK_URL: str = (
    os.getenv("WEBHOOK_URL", "").strip()
    or os.getenv("RENDER_EXTERNAL_URL", "").strip()
)
WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "").strip()

SERVICE_NAME = "Pay Bot"
MIN_AMOUNT = 1
MAX_AMOUNT = 100000
import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from .config import BOT_TOKEN, PAYMENT_POLL_INTERVAL, PORT, WEBHOOK_SECRET, WEBHOOK_URL
from .database import db
from .handlers import admin, fallback, start
from .services.payment_service import PaymentPoller

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

COMMANDS = [
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="admin", description="Панель администратора"),
    BotCommand(command="cancel", description="Отменить действие"),
]

WEBHOOK_PATH = "/webhook"


async def _health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


async def _webhook_handler(request: web.Request, bot: Bot, dp: Dispatcher) -> web.Response:
    if WEBHOOK_SECRET:
        if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
            return web.Response(status=403)
    update = await request.json()
    await dp.feed_webhook_update(bot, update)
    return web.Response(status=200)


async def run_webhook(bot: Bot, dp: Dispatcher, webhook_url: str) -> None:
    path = WEBHOOK_PATH
    await bot.set_webhook(
        url=webhook_url + path,
        secret_token=WEBHOOK_SECRET or None,
        drop_pending_updates=True,
    )
    logger.info("Webhook установлен: %s", webhook_url + path)

    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)
    app.router.add_post(path, lambda req: _webhook_handler(req, bot, dp))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info("HTTP-сервер запущен на порту %s", PORT)

    try:
        await asyncio.Future()
    finally:
        await runner.cleanup()


async def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан. Заполните файл .env")
        return

    await db.init()
    logger.info("База данных: %s", "PostgreSQL (Render)" if db.is_pg else "SQLite (локально)")
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_routers(start.router, admin.router, fallback.router)

    await bot.set_my_commands(COMMANDS)

    poller = PaymentPoller(bot, PAYMENT_POLL_INTERVAL)
    asyncio.create_task(poller.run())
    logger.info("Бот запущен")

    try:
        if WEBHOOK_URL:
            await run_webhook(bot, dp, WEBHOOK_URL.rstrip("/"))
        else:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


def run() -> None:
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
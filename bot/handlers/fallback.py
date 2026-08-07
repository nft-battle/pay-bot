from aiogram import F, Router
from aiogram.types import Message

from ..texts import WELCOME_TEXT
from ..keyboards import main_menu_kb

router = Router()


@router.message(F.text)
async def fallback(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())
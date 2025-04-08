from aiogram import F, Router
from aiogram.types import Message

from keyboards import settings_keyboard

from database import MongoDB


router = Router()

# Обработка кнопки "Настройки"
@router.message(F.text == "Мои настройки")
async def settings_handler(message: Message):
    await message.answer("Настройки", reply_markup=settings_keyboard)
    # await MongoDB().add_user(id=message.from_user.id)
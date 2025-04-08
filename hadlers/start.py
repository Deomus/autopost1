import asyncio
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from keyboards import main_keyboard, settings_keyboard

from database import MongoDB
from worker import infinity_scrolling, infinity_posting
from loguru import logger


router = Router()

# Обработка комманды "/start"
@router.message(CommandStart())
async def command_start_handler(message: Message):
    # await message.answer("Выберите настройки", reply_markup=settings_keyboard)
    
    await message.answer("Для просмотра настроек нажмите 'Мои настройки', для отмены действия нажмите 'Отмена'", reply_markup=main_keyboard)
    await MongoDB().add_user(id=message.from_user.id)
    
    while True:
        doc = await MongoDB().check_user(message.from_user.id)

        if doc:
            # asyncio.create_task(infinity_scrolling(message.from_user.id))
            asyncio.create_task(infinity_posting(message.from_user.id))
            logger.success(f"ID:{message.from_user.id} create infinity_scrolling and infinity_posting")
            break  # Выход из цикла после выполнения функции

        # Если документ не найден или не все поля заполнены, ждем некоторое время
        # logger.info(f"ID:{message.from_user.id} not data, sleep 5 sec...")
        await asyncio.sleep(5)  # Задержка в 5 секунд перед следующей проверкой
    
    
    
    # asyncio.create_task(infinity_scrolling(message.from_user.id, bot))
    # asyncio.create_task(infinity_posting(message.from_user.id, bot))
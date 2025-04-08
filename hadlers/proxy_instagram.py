from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import States
from keyboards import settings_keyboard

from database import MongoDB
from loguru import logger

from utils import pattern_proxy


router = Router()

# Обработка кнопки "Proxy Instagram"
@router.callback_query(F.data == "proxy_instagram")
async def proxy_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # logger.info("proxy")
    
    user = await MongoDB().get_user(id=callback.from_user.id)
    
    if user.proxy_instagram:   
        await callback.message.edit_text(f"Прокси Instagram: {user.proxy_instagram.uri}")
        await callback.message.answer("Введите новый прокси в формате http(s)://user:password@111.222.333.444:55555")
       
        await state.set_state(States.proxy_instagram)
    else:
        await callback.message.edit_text("Прокси Instagram: нет.")
        await callback.message.answer("Введите новый прокси в формате http(s)://user:password@111.222.333.444:55555")

        await state.set_state(States.proxy_instagram)
# Обработка ввода прокси Instagram  
@router.message(States.proxy_instagram)   
async def set_proxy(message: Message, state: FSMContext):
    if pattern_proxy.match(message.text):
    
        await MongoDB().set_proxy_instagram(
            id=message.from_user.id,
            uri=message.text
        )

        await message.answer("Прокси instagram успешно добавлен")
        logger.info(f"ID: {message.from_user.id} add proxy Instagram")
        
        await state.clear()

    else:
        await message.answer("Ошибка при вводе данных, попробуйте еще раз")

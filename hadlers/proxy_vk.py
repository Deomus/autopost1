from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import States

from database import MongoDB
from loguru import logger

from keyboards import settings_keyboard

from utils import pattern_proxy


router = Router()

# Обработка кнопки "Proxy VK"
@router.callback_query(F.data == "proxy_vk")
async def proxy_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # logger.info("proxy")
    
    user = await MongoDB().get_user(id=callback.from_user.id)
    
    if user.proxy_vk:   
        await callback.message.edit_text(f"Прокси VK: {user.proxy_vk.uri}")
        await callback.message.answer("Введите новый прокси в формате http(s)://user:password@111.222.333.444:55555")
       
        await state.set_state(States.proxy_vk)
    else:
        await callback.message.edit_text("Прокси VK: нет.")
        await callback.message.answer("Введите новый прокси в формате http(s)://user:password@111.222.333.444:55555")
        await state.set_state(States.proxy_vk)

# Обработка ввода прокси VK  
@router.message(States.proxy_vk)   
async def set_proxy(message: Message, state: FSMContext):
    if pattern_proxy.match(message.text):
        await MongoDB().set_proxy_vk(
            id=message.from_user.id,
            uri=message.text
        )

        await message.answer("Прокси VK успешно добавлен", reply_markup=settings_keyboard)
        logger.info(f"ID: {message.from_user.id} add proxy VK")
        
        await state.clear()
    else:
        await message.answer("Ошибка при вводе данных, попробуйте еще раз")


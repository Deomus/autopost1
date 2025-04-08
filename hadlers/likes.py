from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import States

from database import MongoDB
from loguru import logger

from keyboards import settings_keyboard



router = Router()

# Обработка кнопки "Порог лайков"
@router.callback_query(F.data == "likes")
async def proxy_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    user = await MongoDB().get_user(id=callback.from_user.id)
   
    await callback.message.edit_text(f"Порог лайков: {user.likes}")
    await callback.message.answer("Введите новый порог для лайков")
    
    await state.set_state(States.likes)

# Обработка ввода лайков   
@router.message(States.likes)   
async def set_likes(message: Message, state: FSMContext):
    if message.text.isdigit():
        await MongoDB().set_likes(
            id = message.from_user.id,  
            likes = message.text
        )
        await message.answer(f"Установлен новый порог {message.text} лайков.", reply_markup=settings_keyboard)
        logger.info(f"ID: {message.from_user.id} set {message.text} likes")
        
        await state.clear()
    else:
        await message.answer("Вы не указали порог")
        
        # await state.set_state(States.likes)       

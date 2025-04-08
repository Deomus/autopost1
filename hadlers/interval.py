from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import States

from database import MongoDB
from loguru import logger
from keyboards import settings_keyboard



router = Router()

# Обработка кнопки "Интервал отправки"
@router.callback_query(F.data == "interval")
async def interval_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    user = await MongoDB().get_user(id=callback.from_user.id)
   
    await callback.message.edit_text(f"Интервал постинга: {user.interval} мин.")
    await callback.message.answer("Введите новый интервал")
    
    await state.set_state(States.interval)

# Обработка ввода интервала постинга
@router.message(States.interval)   
async def set_interval(message: Message, state: FSMContext):
    if message.text.isdigit():
        await MongoDB().set_interval(
            id = message.from_user.id,  
            interval = message.text
        )
        await message.answer(f"Установлен новый интервал {message.text} мин.", reply_markup=settings_keyboard)
        logger.info(f"ID: {message.from_user.id} set {message.text} interval")
        
        await state.clear()
    else:
        await message.answer("Вы не указали интервал")
        
        # await state.set_state(States.interval)       

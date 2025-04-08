from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards import settings_keyboard



router = Router()

# Обработка кнопки "Отмена"
@router.message(F.text == "Отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите один из пунктов меню", reply_markup=settings_keyboard)
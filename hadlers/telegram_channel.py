from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
from database import MongoDB
from keyboards import settings_keyboard

router = Router()

class TelegramChannelStates(StatesGroup):
    waiting_for_channel_id = State()

@router.callback_query(F.data == "telegram_channel")
async def set_telegram_channel(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите `chat_id` твоего Telegram-канала (например: `-1001234567890`):")
    await state.set_state(TelegramChannelStates.waiting_for_channel_id)
    await callback.answer()

@router.message(TelegramChannelStates.waiting_for_channel_id)
async def save_channel_id(message: Message, state: FSMContext):
    try:
        chat_id = int(message.text.strip())
        await MongoDB().add_telegram_channel(id=message.from_user.id, chat_id=chat_id)
        logger.success(f"Пользователь {message.from_user.id} добавил Telegram-канал {chat_id}")
        await message.answer("✅ Канал сохранён", reply_markup=settings_keyboard)
    except Exception as e:
        await message.answer("❌ Ошибка. Проверьте формат и попробуй снова.")
        logger.error(f"Ошибка при добавлении канала: {e}")
    finally:
        await state.clear()

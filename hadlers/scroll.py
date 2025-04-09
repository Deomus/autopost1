import asyncio
from aiogram import F, Router, types
from worker import infinity_scrolling  # функция автоскроллинга из worker.py
from database import MongoDB
from loguru import logger

router = Router()

@router.callback_query(F.data == "start_scrolling")
async def start_scrolling_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # Проверяем, есть ли пользователь в базе
    user = await MongoDB().get_user(user_id)
    if not user:
        await callback.message.answer("❌ Ваш аккаунт не найден в базе. Зарегистрируйтесь, используя /start.")
        await callback.answer()
        return

    # Запускаем автоскроллинг для этого пользователя в виде фоновой задачи
    asyncio.create_task(infinity_scrolling(user_id))
    logger.success(f"Запущен автоскроллинг для пользователя {user_id}")

    await callback.message.answer("✅ Автоскроллинг запущен!")
    await callback.answer()

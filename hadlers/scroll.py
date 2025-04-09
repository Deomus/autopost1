import asyncio
from aiogram import F, Router, types
from worker import infinity_scrolling  # функция автоскроллинга из worker.py
from database import MongoDB
from loguru import logger

router = Router()

# Глобальное хранилище для запущенных задач автоскроллинга
active_scrolling_tasks = {}

@router.callback_query(F.data == "start_scrolling")
async def start_scrolling_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await MongoDB().get_user(user_id)
    if not user:
        await callback.message.answer("❌ Ваш аккаунт не найден в базе. Зарегистрируйтесь, используя /start.")
        await callback.answer()
        return

    # Если автоскроллинг уже запущен, сообщаем об этом
    if user_id in active_scrolling_tasks:
        await callback.message.answer("❗ Автоскроллинг уже запущен для вас!")
        await callback.answer()
        return

    task = asyncio.create_task(infinity_scrolling(user_id))
    active_scrolling_tasks[user_id] = task
    logger.success(f"Запущен автоскроллинг для пользователя {user_id}")

    await callback.message.answer("✅ Автоскроллинг запущен!")
    await callback.answer()

@router.callback_query(F.data == "stop_scrolling")
async def stop_scrolling_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in active_scrolling_tasks:
        await callback.message.answer("Автоскроллинг не запущен для вас!")
        await callback.answer()
        return

    task = active_scrolling_tasks[user_id]
    task.cancel()
    del active_scrolling_tasks[user_id]
    logger.success(f"Остановлен автоскроллинг для пользователя {user_id}")

    await callback.message.answer("✅ Автоскроллинг остановлен!")
    await callback.answer()

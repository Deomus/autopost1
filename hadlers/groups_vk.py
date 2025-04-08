from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import States

from database import MongoDB
from loguru import logger

from keyboards import groups_vk_keyboard, settings_keyboard

from utils import pattern_group_vk



router = Router()

# Обработка кнопки "Группы VK"
@router.callback_query(F.data == "groups_vk")
async def groups_vk_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    user = await MongoDB().get_user(id=callback.from_user.id)
    groups_vk = user.groups_vk

    if groups_vk:
        await callback.message.edit_text(
            "Группы VK:",
            reply_markup=await groups_vk_keyboard(groups_vk)
        )
        await callback.message.answer("Отправьте ссылку на группу для добавления или нажмите на группу, которую хотите удалить")
    else:
        await callback.message.edit_text("Группы VK: нет.")
        await callback.message.answer("Отправьте ссылку на группу")
    
    await state.set_state(States.groups_vk)

# Обработка ввода групп VK
@router.message(States.groups_vk)   
async def set_groups_vk(message: Message, state: FSMContext):
    if pattern_group_vk.match(message.text):
    
        result = await MongoDB().set_groups_vk(
            id=message.from_user.id,  
            url=message.text
        )
        if result.modified_count > 0:
            await message.answer("Группа успешно добавлена.", reply_markup=settings_keyboard)
            await state.clear()
        else:
            await message.answer("Группа уже есть, введите другую группу.")
            
    else:
        await message.answer("Ошибка при вводе данных, попробуйте еще раз.")

# Удаление группы  
@router.callback_query(F.data.startswith("group_"))       
async def groups_vk_delete_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    url = callback.data.replace("group_", "")
    await MongoDB().delete_groups_vk(callback.from_user.id, url)
    logger.info(f"ID: {callback.from_user.id} delete {callback.data}")
    
    user = await MongoDB().get_user(id=callback.from_user.id)
    groups_vk = user.groups_vk

    if groups_vk:
        await callback.message.edit_text(
            "Группы VK:",
            reply_markup=await groups_vk_keyboard(groups_vk)
        )
        await callback.message.answer("Отправьте ссылку на группу для добавления или нажмите на группу, которую хотите удалить")
    else:
        await callback.message.edit_text("Группы VK: нет.")
        await callback.message.answer("Отправьте ссылку на группу")
        
       
       
     

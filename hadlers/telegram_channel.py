from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
from database import MongoDB
from config import settings
from keyboards import settings_keyboard

router = Router()
bot = Bot(token=settings.token)

class TelegramChannelStates(StatesGroup):
    waiting_for_channel_username = State()

@router.callback_query(F.data == "telegram_channel")
async def telegram_channel_handler(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.from_user.id)
    user = await MongoDB().get_user(user_id)
    channels = user.telegram_channels if user and user.telegram_channels else []

    # Клавиатура
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for chat_id in channels:
        try:
            chat = await bot.get_chat(chat_id)
            if chat.username:
                markup.inline_keyboard.append(
                    [InlineKeyboardButton(text=f"@{chat.username}", url=f"https://t.me/{chat.username}")]
                )
            else:
                markup.inline_keyboard.append(
                    [InlineKeyboardButton(text=str(chat.id), callback_data="noop")]
                )
        except Exception as e:
            logger.warning(f"Не удалось получить данные канала {chat_id}: {e}")
            markup.inline_keyboard.append(
                [InlineKeyboardButton(text=str(chat_id), callback_data="noop")]
            )

    # Сообщение
    if channels:
        text = "Добавленные каналы:\n" + "\n".join(
            [f"@{(await bot.get_chat(cid)).username}" if (await bot.get_chat(cid)).username else f"{cid}"
             for cid in channels]
        ) + "\n\n1.Добавьте бота в администраторы канала.\n"
        "2.Введите username нового канала, например: <code>@my_channel</code>"
    else:
        text = "1.Добавьте бота в администраторы канала.\n" \
        "Введите username канала, например: <code>@my_channel</code>"

    await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
    await state.set_state(TelegramChannelStates.waiting_for_channel_username)
    await callback.answer()

@router.message(TelegramChannelStates.waiting_for_channel_username)
async def save_telegram_channel(message: Message, state: FSMContext):
    user_id = int(message.from_user.id)
    raw_input = message.text.strip()
    try:
        if not raw_input.startswith("@"):
            raise ValueError("Введите username канала, начиная с символа @")
        
        chat = await bot.get_chat(raw_input)
        chat_id = chat.id

        bot_info = await bot.get_me()
        member = await bot.get_chat_member(chat_id, bot_info.id)

        if member.status != "administrator":
            raise PermissionError("Бот не является админом в этом канале.")
        if hasattr(member, "can_post_messages") and not member.can_post_messages:
            raise PermissionError("У бота нет прав на публикацию.")

        await MongoDB().add_telegram_channel(user_id, chat_id)
        logger.success(f"Пользователь {user_id} добавил канал {chat_id}")

        await message.answer(
            f"✅ Канал @{chat.username if chat.username else chat_id} добавлен.",
            reply_markup=settings_keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при добавлении канала: {e}")
        await message.answer(
            "❌ Не удалось добавить канал.\n\n"
            "1. Убедитесь, что вы ввели правильный username (например: <code>@my_channel</code>).\n"
            "2. Добавьте бота в канал и дайте ему права администратора.\n"
            "3. Убедитесь, что канал — это именно <b>Telegram-канал</b>, а не чат или группа.",
            parse_mode="HTML"
        )

    finally:
        await state.clear()

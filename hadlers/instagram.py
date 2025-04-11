import asyncio, random
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from playwright.async_api import async_playwright, Playwright
import uuid

from states import States

from database import MongoDB
from loguru import logger

from keyboards import settings_keyboard
from model import User



router = Router()

# Обработка кнопки "Instagram"
@router.callback_query(F.data == "instagram")
async def instagram_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    user: User = await MongoDB().get_user(id=callback.from_user.id)
    
    if user.account_insta:
        account_info = f"Instagram аккаунт\nПользователь: {user.account_insta.login}\nПароль: {user.account_insta.password}"
    else:
        account_info = "Instagram аккаунт: нет."
    
    await callback.message.edit_text(account_info, reply_markup=None)
    
    await callback.message.answer("Введите новые данные")
   
    await state.set_state(States.instagram)
        

# Обработка ввода аакаунта instagram
@router.message(States.instagram)   
async def set_instagram(message: Message, state: FSMContext):
    sent_message = await message.answer("Обработка ввода...")
    
    user = await MongoDB().get_user(message.from_user.id)
    
    data = message.text.split(" ")
    
    proxy_url = user.proxy_instagram.uri

    # Разбираем прокси на компоненты
    proxy_parts = proxy_url.split("://")[1].split("@")
    username_password = proxy_parts[0].split(":")
    host_port = proxy_parts[1]

    proxy = {
        "server": f"http://{host_port}",  # Адрес прокси-сервера
        "username": username_password[0],  # Имя пользователя
        "password": username_password[1]   # Пароль
    }
    if len(data) == 2:
        
        logger.info(f"proxy {proxy}")
        try:
            p = await async_playwright().start()  
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(locale='en-US')
            page = await context.new_page()

            await sent_message.edit_text("Загрузка страницы...")
            await page.goto("https://www.instagram.com/accounts/login")
            await asyncio.sleep(5)
            
            try:
                cookies_heading = await page.get_by_role("heading", name="Allow the use of cookies from").wait_for(timeout=3000)
                if cookies_heading:
                    logger.info("✅ Обнаружено окно cookies — принимаем")
                    await page.get_by_role("button", name="Allow all cookies").click()
                    await asyncio.sleep(1)
            except Exception:
                logger.info("ℹ️ Окно cookies не появилось — продолжаем без него")
            
            await sent_message.edit_text("Ввод данных...")
            await page.get_by_role("textbox", name="Phone number, username, or email").fill(data[0])
            await asyncio.sleep(random.uniform(1.5, 5.5))
            await page.get_by_role("textbox", name="Password").fill(data[1])
            await asyncio.sleep(random.uniform(1.5, 5.5))
            await page.keyboard.press('Enter')
            await sent_message.edit_text("Обработка данных...")
            await asyncio.sleep(10)
            
            # await sent_message.edit_text("Введите код из SMS или WhatsApp")
            
            # await state.update_data(
            #     browser=browser,
            #     context=context,
            #     page=page,
            #     login=data[0],
            #     password=data[1]
            # )
            
            # await state.set_state(States.instagram_2fa)
            
            
            
            cookies = await context.cookies()
        
            await MongoDB().add_account_insta(
                id=message.from_user.id,
                login=data[0],
                password=data[1],
                cookies=cookies
            )

            logger.success(f"ID: {message.from_user.id} Успешный вход в Instagram")
            await message.answer("Успешный вход в Instagram", reply_markup=settings_keyboard)
                        
        except Exception as e:
            logger.error(f"Ошибка при входе: {e}")
            await page.screenshot(path=f"./errors/insta_{message.from_user.id}_{uuid.uuid4()}.png", full_page=True)
            
            await message.answer(f"Ошибка регистрации попробуйте еще раз, введи данные")
        
        finally:
            # Закрываем браузер и очищаем состояние
            await browser.close()
            await state.clear()

    else:
        await message.answer("Некорректный ввод")
        
        # await state.set_state(States.instagram)       


@router.message(States.instagram_2fa)
async def set_instagram_2fa(message: Message, state: FSMContext):
    # Получаем код от пользователя
    code = message.text.strip()

    # Получаем данные из состояния (если нужно)
    data = await state.get_data()
    browser = data.get("browser")
    context = data.get("context")
    page = data.get("page")
    login = data.get("login")
    password = data.get("password")

    if not browser or not context or not page:
        await message.answer("Ошибка: сессия не найдена. Попробуйте войти снова.")
        await state.clear()
        return

    try:
        sent_msg = await message.answer("Ввод кода...")
        # Вводим код на странице Instagram
        await page.get_by_role("textbox", name="Security Code").fill(code)
        await asyncio.sleep(random.uniform(1.5, 5.5))
        await page.keyboard.press('Enter')
        await asyncio.sleep(10)
        await sent_msg.edit_text("Обработка кода...")
        await page.keyboard.press('Enter')
        await asyncio.sleep(5)
        await page.keyboard.press('End')
        await asyncio.sleep(5)
        await page.keyboard.press('End')
        await asyncio.sleep(10)
        
        cookies = await context.cookies()
        
        await MongoDB().add_account_insta(
            id=message.from_user.id,
            login=login,
            password=password,
            cookies=cookies
        )

        logger.success(f"ID: {message.from_user.id} Успешный вход в Instagram")
        
        await message.answer("Успешный вход в Instagram", reply_markup=settings_keyboard)

    except Exception as e:
        logger.error(f"Ошибка при вводе кода: {e}")
        await page.screenshot(path=f"./errors/insta_{message.from_user.id}_{uuid.uuid4()}.png", full_page=True)
        await message.answer("Произошла ошибка. Попробуйте снова.")

    finally:
        # Закрываем браузер и очищаем состояние
        await browser.close()
        await state.clear()
import asyncio, random
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from playwright.async_api import async_playwright
import uuid

from states import States

from database import MongoDB
from loguru import logger

from keyboards import settings_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.state import State, StatesGroup

class States(StatesGroup):
    vk = State()
    vk_2fa = State()
    vk_backup = State()

router = Router()

# Обработка кнопки "vk"
@router.callback_query(F.data == "vk")
async def vk_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    user = await MongoDB().get_user(id=callback.from_user.id)
    if user.account_vk:
        await callback.message.edit_text(
            f"VK аккаунт\nПользователь: {user.account_vk.login}\nПароль: {user.account_vk.password}\nВведите новые данные",
            reply_markup=None
        )
        await state.set_state(States.vk)
    else:
        await callback.message.edit_text(
            "VK аккаунт: нет\nВведите новые данные логин/телефон (10 цифр) и пароль"
        )
        await state.set_state(States.vk)


# Обработка ввода аккаунта VK
@router.message(States.vk)
async def set_vk(message: Message, state: FSMContext):
    user = await MongoDB().get_user(message.from_user.id)
    data = message.text.split(" ")

    proxy_url = user.proxy_vk.uri
    proxy_parts = proxy_url.split("://")[1].split("@")
    username_password = proxy_parts[0].split(":")
    host_port = proxy_parts[1]

    proxy = {
        "server": f"http://{host_port}",
        "username": username_password[0],
        "password": username_password[1]
    }

    if len(data) == 2:
        sent_message = await message.answer("Загрузка страницы...")
        try:
            login = data[0]
            password = data[1]
            p = await async_playwright().start()
            browser = await p.chromium.launch(headless=True, proxy=proxy)
            context = await browser.new_context(locale='en-US')
            page = await context.new_page()

            await page.goto("https://vk.com/")
            await asyncio.sleep(5)
            await sent_message.edit_text("Ввод данных...")

            await page.get_by_test_id("enter-another-way").click()
            await asyncio.sleep(random.uniform(1.5, 5.5))
            await page.get_by_role("textbox", name="+7 000 000 00").fill(login)
            await asyncio.sleep(random.uniform(1.5, 5.5))

            await sent_message.edit_text("Обработка данных...")
            await asyncio.sleep(1)
            await page.locator("[data-test-id=\"submit_btn\"]").click()

            markup = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="SMS код", callback_data="vk_2fa_sms"),
                    InlineKeyboardButton(text="Бэкап код", callback_data="vk_2fa_backup")
                ]
            ])
            await sent_message.edit_text("Выберите способ подтверждения входа:", reply_markup=markup)

            await state.update_data(
                browser=browser,
                context=context,
                page=page,
                login=login,
                password=password
            )

        except Exception as e:
            logger.error(f"Ошибка при входе: {e}")

    else:
        await message.answer("Некорректный ввод")


@router.callback_query(F.data == "vk_2fa_sms")
async def vk_2fa_sms(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите код из SMS")
    await state.set_state(States.vk_2fa)


@router.callback_query(F.data == "vk_2fa_backup")
async def vk_2fa_backup(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ваш бэкап-код")
    await state.set_state(States.vk_backup)


@router.message(States.vk_2fa)
async def set_vk_2fa(message: Message, state: FSMContext):
    code = message.text.strip()
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
        for i, digit in enumerate(code[:6]):
            selector = f"div:nth-child({i+1}) > div > .vkc__TextField__wrapper > .vkc__TextField__input"
            await page.locator(selector).fill(digit)
            await asyncio.sleep(1)

        await asyncio.sleep(2)
        await page.get_by_role("textbox", name="Enter password").fill(password)
        await asyncio.sleep(1)
        await page.get_by_role("button", name="Continue").click()
        await asyncio.sleep(5)

        cookies = await context.cookies()
        await MongoDB().add_account_vk(
            id=message.from_user.id,
            login=login,
            password=password,
            cookies=cookies
        )

        logger.success(f"ID: {message.from_user.id} Успешный вход в VK")
        await message.answer("Успешный вход в VK", reply_markup=settings_keyboard)

    except Exception as e:
        logger.error(f"Ошибка при вводе кода: {e}")
        await page.screenshot(path=f"./errors/vk_2fa_{uuid.uuid4()}.png", full_page=True)
        await message.answer("Произошла ошибка. Попробуйте снова.")

    finally:
        await browser.close()
        await state.clear()


@router.message(States.vk_backup)
async def set_vk_backup(message: Message, state: FSMContext):
    backup_code = message.text.strip()
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
        await message.answer("Ввод бэкап-кода...")

        await page.locator("[data-test-id=\"other-verification-methods\"]").click()
        await page.locator("[data-test-id=\"verificationMethod_reserve_code\"]").click()
        await asyncio.sleep(1)

        await page.locator(".vkc__TextField__input").first.click()
        await asyncio.sleep(0.5)
        await page.locator(".vkc__TextField__input").first.fill(backup_code)
        await asyncio.sleep(1)

        await page.get_by_role("button", name="Continue").click()
        await asyncio.sleep(2)

        await asyncio.sleep(2)
        await page.get_by_role("textbox", name="Enter password").fill(password)
        await asyncio.sleep(1)
        await page.get_by_role("button", name="Continue").click()
        await asyncio.sleep(5)

        cookies = await context.cookies()
        await MongoDB().add_account_vk(
            id=message.from_user.id,
            login=login,
            password=password,
            cookies=cookies
        )

        logger.success(f"ID: {message.from_user.id} Успешный вход в VK по бэкап-коду")
        await message.answer("Успешный вход в VK", reply_markup=settings_keyboard)

    except Exception as e:
        logger.error(f"Ошибка при вводе бэкап-кода: {e}")
        await page.screenshot(path=f"./errors/vk_backup_{uuid.uuid4()}.png", full_page=True)
        await message.answer("Произошла ошибка при вводе бэкап-кода. Попробуйте снова.")

    finally:
        await browser.close()
        await state.clear()

import os, asyncio
import aiohttp
import uuid
from playwright.async_api import async_playwright
from selectolax.lexbor import LexborHTMLParser
from pprint import pprint as pp
from database import MongoDB
from loguru import logger
from redis.asyncio import Redis
from aiogram import Bot
from config import settings




from aiogram.types import FSInputFile

postcard = "div.x1qjc9v5.x9f619.x78zum5.xg7h5cd.x1xfsgkm.xqmdsaz.x1bhewko.xgv127d.xh8yej3.xl56j7k"
likes = "span.html-span.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1hl2dhg.x16tdsg8.x1vvkbs"

r = Redis(host='localhost', port=6379, db=0)

def convert_string_to_number(s: str):
    if "K" in s:
        number = float(s[:-1])
        return int(number * 1000)
    elif "M" in s:
        number = float(s[:-1])
        return int(number * 1000000)
    else:
        return 0

async def download_video(url: str, output_path: str, proxy_url: str = None, headers=None):
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, proxy=proxy_url) as response:
                if response.status == 200:
                    with open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(1024):
                            f.write(chunk)
                    logger.info(f"✅ Видео сохранено в {output_path}")
                else:
                    logger.error(f"⚠️ Ошибка {response.status}: не удалось скачать видео")
    except Exception as e:
        logger.error(f"ID: {id} Ошибка при скачивании видео: {e}")

async def infinity_scrolling(id: str):
    logger.info(f"Начало бесконечного скроллинга для пользователя с id {id}")
    async with async_playwright() as playwright:
        user = await MongoDB().get_user(id)
        if not user:
            logger.error(f"Пользователь с id {id} не найден")
            return

        proxy_url = user.proxy_instagram.uri
        proxy_parts = proxy_url.split("://")[1].split("@")
        username_password = proxy_parts[0].split(":")
        host_port = proxy_parts[1]

        proxy = {
            "server": f"http://{host_port}",
            "username": username_password[0],
            "password": username_password[1]
        }

        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(locale='en-US')

        if user:
            await context.add_cookies(user.account_insta.cookies)

        while True:
            page = None
            try:
                page = await context.new_page()
                await page.goto("https://www.instagram.com/reels/")
                await asyncio.sleep(5)
                await page.keyboard.press('Enter')
                await asyncio.sleep(1)

                viewport_size = page.viewport_size
                center_x = viewport_size['width'] / 2
                center_y = viewport_size['height'] / 2
                await page.mouse.click(center_x, center_y)

                user = await MongoDB().get_user(id)
                if not user:
                    logger.error(f"ID: {id} Пользователь не найден")
                    break

                queue_len = len(user.queue)
                while queue_len < 5:
                    await asyncio.sleep(2)
                    html = await page.content()
                    parser = LexborHTMLParser(html)

                    if postcards := parser.css(postcard):
                        logger.info(f"кол-во постов {len(postcards)}")
                        for card in postcards:
                            if video := card.css_first("video"):
                                like = convert_string_to_number(card.css_first(likes).text())
                                if like > user.likes:
                                    video_url = video.attrs['src']
                                    logger.info(f"ссылка {video_url}")
                                    if await r.sadd(id, video_url):
                                        logger.info(f"ID: {id} LIKE_DONE: {like}")
                                        filepath = f"./downloads/{uuid.uuid4()}.mp4"
                                        try:
                                            await download_video(video_url, filepath)
                                            await MongoDB().add_to_queue(id, filepath)
                                        except Exception as e:
                                            logger.error(f"ID: {id} Ошибка при скачивании: {e}")
                                            continue
                                        await asyncio.sleep(5)
                                    else:
                                        logger.info(f"ID: {id} Видео уже в Redis: {video_url}")
                            else:
                                logger.warning("нет ссылки на видео")

                        await page.keyboard.press('End')
                        await asyncio.sleep(3)
                        user = await MongoDB().get_user(id)
                        queue_len = len(user.queue)
                    else:
                        logger.info(f"ID: {id} Нет новых видео")

                logger.info(f"ID: {id} Очередь заполнена, ожидание 5 минут")
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"ID: {id} Ошибка в бесконечном скроллинге: {e}")
                await asyncio.sleep(15)
            finally:
                if page and not page.is_closed():
                    await page.close()

async def infinity_posting(id: str):
    bot = Bot(token=settings.token)
    logger.info(f"ID: {id} start posting")

    while True:
        try:
            async with async_playwright() as playwright:
                user = await MongoDB().get_user(id)
                if not user or not user.queue:
                    logger.info(f"ID: {id} Очередь пуста, спим 60 сек...")
                    await asyncio.sleep(60)
                    continue

                # Настраиваем прокси для VK
                proxy_url = user.proxy_vk.uri
                proxy_parts = proxy_url.split("://")[1].split("@")
                username_password = proxy_parts[0].split(":")
                host_port = proxy_parts[1]
                proxy = {
                    "server": f"http://{host_port}",
                    "username": username_password[0],
                    "password": username_password[1]
                }

                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context(locale='en-US')
                await context.add_cookies(user.account_vk.cookies)
                page = await context.new_page()

                while user.queue:
                    filepath = user.queue[0]
                    success_vk = True
                    success_tg = True

                    # --- POST TO VK ---
                    try:
                        for group in user.groups_vk:
                            await page.goto(group.url)
                            await asyncio.sleep(5)
                            logger.info(f"ID: {id} VK → {group.url}")

                            await page.get_by_test_id("posting_create_post_button").click()
                            await asyncio.sleep(1)
                            await page.get_by_text("Загрузить с устройства").click()
                            await asyncio.sleep(1)
                            await page.get_by_test_id("posting_base_screen_download_from_device").set_input_files(filepath)
                            await asyncio.sleep(1)
                            await page.get_by_test_id("posting_base_screen_next").click()
                            await asyncio.sleep(1)
                            await page.get_by_test_id("posting_submit_button").click()
                            await asyncio.sleep(1)

                            logger.info(f"ID: {id} отправлено в VK: {group.url}")
                            await asyncio.sleep(user.interval * 60)
                    except Exception as e:
                        logger.error(f"ID: {id} ❌ Ошибка VK: {e}")
                        success_vk = False

                    # --- POST TO TELEGRAM ---
                    try:
                        if user.telegram_channels:
                            for channel_id in user.telegram_channels:
                                try:
                                    # Формируем корректный InputFile для aiogram
                                    video_file = FSInputFile(filepath)
                                    await bot.send_video(
                                        chat_id=channel_id,
                                        video=video_file,
                                        caption=""
                                    )
                                    logger.info(f"ID: {id} отправлено в Telegram {channel_id}")
                                except Exception as tg_err:
                                    logger.error(f"ID: {id} ❌ Ошибка Telegram канал {channel_id}: {tg_err}")
                                    success_tg = False
                    except Exception as e:
                        logger.error(f"ID: {id} ❌ Ошибка Telegram блока: {e}")
                        success_tg = False

                    # --- Удаляем, только если отправка успешна во всех каналах ---
                    if success_vk or success_tg:
                        await MongoDB().delete_from_queue(id, filepath)
                        logger.info(f"ID: {id} удалено из очереди: {filepath}")

                        if os.path.exists(filepath):
                            os.remove(filepath)
                            logger.info(f"ID: {id} удалено с диска: {filepath}")
                        else:
                            logger.warning(f"ID: {id} файл {filepath} не найден")
                    else:
                        logger.warning(f"ID: {id} ❌ Видео не отправлено во все каналы — оставляем в очереди")

                    # Обновляем данные пользователя для следующей итерации
                    user = await MongoDB().get_user(id)

                # Закрываем контекст и браузер (при выходе из внутреннего цикла)
                await context.close()
                await browser.close()

            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"ID: {id} Ошибка в infinity_posting: {e}")
            await asyncio.sleep(15)

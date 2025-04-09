import os, asyncio
import aiohttp
import uuid
from playwright.async_api import async_playwright
from selectolax.lexbor import LexborHTMLParser
from pprint import pprint as pp
from database import MongoDB
from loguru import logger
from redis.asyncio import Redis

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

        browser = await playwright.chromium.launch(headless=False)
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
                                await page.screenshot(path=f"debug_{uuid.uuid4()}.png")

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
    logger.info(f"ID: {id} start posting")
    while True:
        try:
            async with async_playwright() as playwright:
                user = await MongoDB().get_user(id)
                proxy_url = user.proxy_vk.uri
                proxy_parts = proxy_url.split("://")[1].split("@")
                username_password = proxy_parts[0].split(":")
                host_port = proxy_parts[1]

                proxy = {
                    "server": f"http://{host_port}",
                    "username": username_password[0],
                    "password": username_password[1]
                }

                browser = await playwright.chromium.launch(headless=False)
                context = await browser.new_context(locale='en-US')
                await context.add_cookies(user.account_vk.cookies)
                page = await context.new_page()
                user = await MongoDB().get_user(id)

                while len(user.queue) != 0:
                    for group in user.groups_vk:
                        await page.goto(group.url)
                        await asyncio.sleep(5)
                        logger.info(f"ID: {id} download page {group.url}")

                        await page.get_by_test_id("posting_create_post_button").click()
                        await asyncio.sleep(1)
                        await page.get_by_text("Загрузить с устройства").click()
                        await asyncio.sleep(1)
                        await page.get_by_test_id("posting_base_screen_download_from_device").set_input_files(user.queue[0])
                        await asyncio.sleep(1)
                        await page.get_by_test_id("posting_base_screen_next").click()
                        await asyncio.sleep(1)
                        await page.get_by_test_id("posting_submit_button").click()
                        await asyncio.sleep(1)
                        logger.info(f"ID: {id} posting video: {user.queue[0]} in {group.url}")

                        await MongoDB().delete_from_queue(id, user.queue[0])
                        logger.info(f"ID: {id} delete video from queue_db: {user.queue[0]}")

                        if os.path.exists(user.queue[0]):
                            os.remove(user.queue[0])
                            logger.info(f"ID: {id} delete video from downloads: {user.queue[0]}")
                        else:
                            logger.info(f"ID: {id} not exists video: {user.queue[0]}")

                        await asyncio.sleep(user.interval * 60)
                        user = await MongoDB().get_user(id)

            logger.info(f"ID: {id} not video for posting, sleep 60 sec...")
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"ID: {id} Ошибка в infinity_posting: {e}")
            await asyncio.sleep(15)

import asyncio
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings

from hadlers.start import router as start_router
from hadlers.cancel import router as cancel_router
from hadlers.settings import router as settings_router
from hadlers.likes import router as likes_router
from hadlers.interval import router as interval_router
from hadlers.instagram import router as instagram_router
from hadlers.vk import router as vk_router
from hadlers.proxy_instagram import router as proxy_instagram_router
from hadlers.proxy_vk import router as proxy_vk_router
from hadlers.groups_vk import router as groups_vk_router
from hadlers.video_url import router as video_url_router


from database import MongoDB
from loguru import logger
from worker import infinity_posting, infinity_scrolling



dp = Dispatcher()
bot = Bot(
    token=settings.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

async def on_startup():
    ids_users = await MongoDB().get_ids_users()
    logger.info(f"ids: {ids_users}")
    
    if ids_users:
        for id_user in ids_users:
            if await MongoDB().check_user(id_user["id"]):
                asyncio.create_task(infinity_scrolling(id_user["id"]))
                asyncio.create_task(infinity_posting(id_user["id"]))
                logger.success(f"ID:{id_user["id"]} create infinity_scrolling and infinity_posting")
                
    
        
    


async def main():
    dp.include_routers(
        start_router,
        cancel_router,
        settings_router,
        likes_router,
        interval_router,
        instagram_router,
        vk_router,
        proxy_instagram_router,
        proxy_vk_router,
        groups_vk_router,
        video_url_router
    )

    dp.startup.register(on_startup)
    
    await dp.start_polling(bot)

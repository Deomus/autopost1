# import data_models
from typing import List
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from model import Community



main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мои настройки")],
        [KeyboardButton(text="Отмена")],
    ],
    resize_keyboard=True,
)

settings_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Proxy Instagram", callback_data="proxy_instagram")],
    [InlineKeyboardButton(text="Instagram", callback_data="instagram")],
    [InlineKeyboardButton(text="Proxy VK", callback_data="proxy_vk")],
    [InlineKeyboardButton(text="VK", callback_data="vk")],
    [InlineKeyboardButton(text="Группы VK", callback_data="groups_vk")],
    [InlineKeyboardButton(text="Порог лайков", callback_data="likes")],
    [InlineKeyboardButton(text="Интервал отправки", callback_data="interval")],
    [InlineKeyboardButton(text="Начать скроллинг", callback_data="start_scrolling")],
])


# skip_date_back = InlineKeyboardMarkup(
#     inline_keyboard=[[InlineKeyboardButton(
#         text="Пропустить",
#         callback_data="skip"
#     )]],
#     resize_keyboard=True,
# )

async def groups_vk_keyboard(groups: list[Community]):
    keyboard = InlineKeyboardBuilder()
    for group in groups:
        keyboard.add(InlineKeyboardButton(
            text = group.url,
            callback_data = f"group_{group.url}"
        ))
    return keyboard.adjust(1).as_markup()

# async def route_button(route: data_models.Route):
#     keyboard = InlineKeyboardBuilder()
#     keyboard.add(InlineKeyboardButton(
#         text = route.number,
#         callback_data = route.id
#     ))
#     return keyboard.adjust(1).as_markup()







# async def inline_routes(routes):
#     keyboard = InlineKeyboardBuilder()
#     for route in routes:
#         src = route["src"].split("_")[0]
#         dst = route["dst"].split("_")[0]
#         keyboard.add(
#             InlineKeyboardButton(
#                 text=f"{src} - {dst} {route['date']}", callback_data=str(route["_id"])
#             )
#         )
#     return keyboard.adjust(1).as_markup()


# async def inline_routes_description(routes):
#     keyboard = InlineKeyboardBuilder()
#     for route in routes:
#         # src = route['src'].split("_")[0]
#         # dst = route['dst'].split("_")[0]
#         keyboard.add(
#             InlineKeyboardButton(
#                 text=route_print(route), callback_data=route["number_route"]
#             )
#         )
#     return keyboard.adjust(1).as_markup()


# async def inline_type_seats(seats):
#     keyboard = InlineKeyboardBuilder()
#     for k, seat in enumerate(seats):
#         keyboard.add(
#             InlineKeyboardButton(
#                 text=f"{seat}",
#                 callback_data=translit(f"{seat}", language_code="ru", reversed=True),
#             )
#         )
#     keyboard.add(InlineKeyboardButton(text=f"Далее", callback_data="done"))
#     return keyboard.adjust(1).as_markup()

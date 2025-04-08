from aiogram.fsm.state import State, StatesGroup




class States(StatesGroup):
    proxy_instagram = State()
    proxy_vk = State()
    instagram = State()
    instagram_2fa = State()
    vk = State()
    vk_2fa = State()
    groups_vk = State()
    interval = State()
    likes = State()
    video_url = State()

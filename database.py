from typing import List, Optional
import motor.motor_asyncio
from dataclasses import asdict
from model import User, Community, AccountInsta, AccountVK, Proxy
from loguru import logger
from config import settings




class MongoDB:
    _instance: Optional['MongoDB'] = None
    _client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
    _users: Optional[motor.motor_asyncio.AsyncIOMotorCollection] = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_uri)
            cls._users = cls._client.telegram.users
        return cls._instance

    @classmethod
    async def add_user(cls, id: str) -> None:
        await cls._users.update_one(
            {"id": id},
            {"$setOnInsert": User(id=id).model_dump()},
            upsert=True
        )
        
    @classmethod
    async def get_user(cls, id: str) -> Optional[User]:
        if user := await cls._users.find_one({"id": id}, {"_id": 0}):
            return User(**user)
        return None
  
    @classmethod
    async def get_ids_users(cls):
        return await cls._users.find({}, {"id": 1, "_id": 0}).to_list()
    
    @classmethod
    async def set_interval(cls, id: str, interval: str) -> None:
        await cls._users.update_one(
            {"id": id},  
            {'$set': {'interval': int(interval)}}
        )
        
    @classmethod
    async def set_likes(cls, id: str, likes: str) -> None:
        await cls._users.update_one(
            {"id": id},  
            {'$set': {'likes': int(likes)}}
        )
  
    # @classmethod
    # async def add_community(cls, id: str, communities: List[Community]) -> None:
    #     communities_dicts = [asdict(community) for community in communities]
    #     await cls._users.update_one(
    #         {"id": id},  
    #         {'$addToSet': {'communities': {'$each': communities_dicts}}}
    #     )

    # @classmethod
    # async def get_communities(cls, id: str) -> Optional[List[Community]]:
    #     user = await cls.get_user(id)
    #     return [Community(**community) for community in user.communities] if user else None
    
    # @classmethod
    # async def remove_community(cls, id: str, title: str) -> bool:
    #     logger.info(title)
    #     result = await cls._users.update_one(
    #         {"id": id},
    #         {"$pull": {"communities": {"title": title}}}
    #     )
    #     logger.info(f"{title}, modified: {result.modified_count}")
    #     return result.modified_count > 0
    
    @classmethod
    async def add_account_insta(
        cls,
        id: str,
        login: str,
        password: str,
        cookies: list
    ):
        await cls._users.update_one(
            {"id": id},  
            {'$set': {'account_insta': AccountInsta(
                login=login,
                password=password,
                cookies=cookies
            ).model_dump()}}
        )
    
    @classmethod
    async def add_account_vk(
        cls,
        id: str,
        login: str,
        password: str,
        cookies: list
    ):
        await cls._users.update_one(
            {"id": id},  
            {'$set': {'account_vk': AccountVK(login=login, password=password, cookies=cookies).model_dump()}}
        )

    @classmethod
    async def add_telegram_channel(cls, id: int, chat_id: int):
        await cls._users.update_one(
            {"id": id},
            {"$addToSet": {"telegram_channels": chat_id}},
            upsert=True
        )

        
    @classmethod
    async def set_groups_vk(cls, id: str, url: str):
        return await cls._users.update_one(
            {"id": id},  
            {'$addToSet': {'groups_vk': Community(url=url).model_dump()}}
        )
        
    @classmethod    
    async def get_groups_vk(cls, id: str,) -> list[Community]:
        return await cls._users.find(
            {"id": id},
            {"groups_vk": 1}).to_list()   
    
    @classmethod
    async def delete_groups_vk(cls, id: str, url: str):
        await cls._users.update_one(
            {"id": id},  
            {'$pull': {'groups_vk': Community(url=url).model_dump()}}
        )
        
    @classmethod
    async def add_to_queue(cls, id, file: str):
        await cls._users.update_one(
            {"id": id},  
            {'$push': {'queue': file}}
        )
        
    @classmethod
    async def delete_from_queue(cls, id: str, filepath: str):
        await cls._users.update_one(
            {"id": id},  
            {'$pull': {'queue': filepath}}
        )

    @classmethod
    async def set_proxy_instagram(
        cls,
        id: str,
        uri: str
    ):
        await cls._users.update_one(
            {"id": id},  
            {'$set': {'proxy_instagram': Proxy(uri=uri).model_dump()}}
        )
   
    @classmethod
    async def set_proxy_vk(
        cls,
        id: str,
        uri: str,
    ):
        await cls._users.update_one(
            {"id": id},  
            {'$set': {'proxy_vk': Proxy(uri=uri).model_dump()}}
        )
    
    @classmethod
    async def check_user(
        cls,
        id: str,
    ):   
        return await cls._users.find_one(
            {
                "id": id,
                "proxy_instagram": {"$ne": None},
                "proxy_vk": {"$ne": None},
                "account_insta": {"$ne": None},
                "account_vk": {"$ne": None}
            }
        )

    @classmethod
    async def close(cls):
        if cls._client:
            cls._client.close()
            cls._instance = None
            cls._client = None
            cls._users = None
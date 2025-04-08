from typing import List, Optional
from pydantic import BaseModel

class Account(BaseModel):
    login: str
    password: str

class Proxy(BaseModel):
    uri: str

class AccountVK(Account):
    cookies: List[dict] = []

class AccountInsta(Account):
    cookies: List[dict] = []

class Community(BaseModel):
    url: str

class User(BaseModel):
    id: int
    proxy_instagram: Optional[Proxy] = None
    proxy_vk: Optional[Proxy] = None
    account_insta: Optional[AccountInsta] = None
    account_vk: Optional[AccountVK] = None
    groups_vk: List[Community] = []
    interval: int = 5
    likes: int = 100000
    queue: List[str] = []
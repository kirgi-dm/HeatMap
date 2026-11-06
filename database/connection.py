from pathlib import Path

from beanie import Document, PydanticObjectId, init_beanie
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo import AsyncMongoClient

from models import Order, OrderCreate, User, UserCreate


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
    )
    DATABASE_URL: str = "mongodb://localhost:27017/heatmap"

    async def initialize_database(self) -> AsyncMongoClient:
        client = AsyncMongoClient(self.DATABASE_URL, serverSelectionTimeoutMS=5000)
        try:
            await init_beanie(
                database=client.get_default_database(), document_models=[User, Order]
            )
        except Exception:
            await client.close()
            raise
        return client


class StorageError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class Database:

    def __init__(self, model: type[Document]):
        self.model = model

    async def save(self, document: Document):
        return await document.create()

    async def get(self, id: PydanticObjectId):
        return await self.model.get(id)

    async def get_all(self):
        return await self.model.find_all().sort("_id").to_list()

    async def update(self, id: PydanticObjectId, body: BaseModel):
        document = await self.get(id)
        if document is None:
            return None
        changes = body.model_dump(exclude_unset=True, exclude_none=True)
        if changes:
            await document.update({"$set": changes})
        return document

    async def delete(self, id: PydanticObjectId):
        document = await self.get(id)
        if document is not None:
            await document.delete()
        return document


class HeatMapDatabase:

    def __init__(self):
        self.users = Database(User)
        self.orders = Database(Order)

    async def list_users(self):
        return await self.users.get_all()

    async def list_orders(self):
        return await self.orders.get_all()

    async def get_user(self, user_id: PydanticObjectId):
        user = await self.users.get(user_id)
        if user is None:
            raise StorageError("Пользователь не найден", 404)
        return user

    async def get_order(self, order_id: PydanticObjectId):
        order = await self.orders.get(order_id)
        if order is None:
            raise StorageError("Заказ не найден", 404)
        return order

    async def create_user(self, data: UserCreate):
        return await self.users.save(User(**data.model_dump()))

    async def update_user(self, user_id: PydanticObjectId, data: BaseModel):
        await self.get_user(user_id)
        return await self.users.update(user_id, data)

    async def delete_user(self, user_id: PydanticObjectId):
        await self.get_user(user_id)
        if await Order.find_one(Order.user_id == user_id) is not None:
            raise StorageError(
                "У пользователя есть заказы. Сначала удалите их или назначьте другому пользователю.",
                409,
            )
        return await self.users.delete(user_id)

    async def create_order(self, data: OrderCreate):
        await self.get_user(data.user_id)
        return await self.orders.save(Order(**data.model_dump()))

    async def update_order(self, order_id: PydanticObjectId, data: BaseModel):
        await self.get_order(order_id)
        if data.user_id is not None:
            await self.get_user(data.user_id)
        return await self.orders.update(order_id, data)

    async def delete_order(self, order_id: PydanticObjectId):
        await self.get_order(order_id)
        return await self.orders.delete(order_id)


db = HeatMapDatabase()

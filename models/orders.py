from beanie import Document, PydanticObjectId
from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class OrderCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"example": {"name": "Первый заказ", "user_id": "507f1f77bcf86cd799439011"}},
    )

    name: str = Field(min_length=1, max_length=200)
    user_id: PydanticObjectId

    @classmethod
    async def as_form(
        cls,
        name: str = Form(..., min_length=1, max_length=200),
        user_id: PydanticObjectId = Form(...),
    ):
        try:
            return cls(name=name, user_id=user_id)
        except ValidationError as error:
            raise RequestValidationError(error.errors()) from error


class OrderUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    user_id: PydanticObjectId | None = None


class Order(Document, OrderCreate):
    class Settings:
        name = "orders"
        indexes = ["user_id"]

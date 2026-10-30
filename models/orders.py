from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlmodel import Field as SQLField, SQLModel


class OrderCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"example": {"name": "Первый заказ", "user_id": 1}},
    )

    name: str = Field(min_length=1, max_length=200)
    user_id: int = Field(gt=0)

    @classmethod
    async def as_form(
        cls,
        name: str = Form(..., min_length=1, max_length=200),
        user_id: int = Form(..., gt=0),
    ):
        try:
            return cls(name=name, user_id=user_id)
        except ValidationError as error:
            raise RequestValidationError(error.errors()) from error


class Order(OrderCreate):
    id: int = Field(gt=0, examples=[1])


class OrderTable(SQLModel, table=True):
    __tablename__ = "orders"
    __table_args__ = {"sqlite_autoincrement": True}

    id: int | None = SQLField(default=None, primary_key=True)
    name: str = SQLField(max_length=200)
    user_id: int = SQLField(foreign_key="users.id", index=True, ondelete="RESTRICT")

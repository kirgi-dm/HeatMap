from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationError
from sqlmodel import Field as SQLField, SQLModel


class UserCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {"username": "Дмитрий", "email": "dmitry@example.com"}
        },
    )

    username: str = Field(min_length=1, max_length=100)
    email: EmailStr

    @classmethod
    async def as_form(
        cls,
        username: str = Form(..., min_length=1, max_length=100),
        email: EmailStr = Form(...),
    ):
        try:
            return cls(username=username, email=email)
        except ValidationError as error:
            raise RequestValidationError(error.errors()) from error


class User(UserCreate):
    id: int = Field(gt=0, examples=[1])


class UserTable(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"sqlite_autoincrement": True}

    id: int | None = SQLField(default=None, primary_key=True)
    username: str = SQLField(max_length=100)
    email: str

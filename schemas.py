from pydantic import BaseModel


class User(BaseModel):
    username: str
    email: str


class Order(BaseModel):
    user: User
    name: str
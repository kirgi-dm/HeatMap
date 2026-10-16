from fastapi import Form
from pydantic import BaseModel


class User(BaseModel):
    username: str
    email: str

    @classmethod
    def as_form(cls, username: str = Form(...), email: str = Form(...)):
        return cls(username=username, email=email)


class Order(BaseModel):
    user: User
    name: str

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        username: str = Form(...),
        email: str = Form(...),
    ):
        return cls(user=User(username=username, email=email), name=name)

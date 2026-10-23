from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from database.connection import db
from dependencies import templates
from models.users import User, UserCreate

user_router = APIRouter(tags=["Пользователи"])


@user_router.get("/users", response_class=HTMLResponse)
async def get_users(request: Request):
    return templates.TemplateResponse(
        request=request, name="users.html", context={"users": list(db.users.values())}
    )


@user_router.post("/user", response_class=RedirectResponse)
async def create_user(request: Request, user: UserCreate = Depends(UserCreate.as_form)):
    db.create_user(user)
    return RedirectResponse(url=request.url_for("get_users"), status_code=303)


@user_router.get("/user/{user_id}", response_class=HTMLResponse)
async def get_user(request: Request, user_id: int, edit: bool = False):
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={"user": db.get_user(user_id), "editing": edit},
    )


@user_router.put("/user/{user_id}", response_model=User)
async def update_user(user_id: int, user: UserCreate):
    return db.update_user(user_id, user)


@user_router.delete("/user/{user_id}", response_model=User)
async def delete_user(user_id: int):
    return db.delete_user(user_id)


@user_router.post("/user/{user_id}/edit", response_class=RedirectResponse)
async def save_user(
    request: Request, user_id: int, user: UserCreate = Depends(UserCreate.as_form)
):
    db.update_user(user_id, user)
    return RedirectResponse(url=request.url_for("get_users"), status_code=303)


@user_router.post("/user/{user_id}/delete", response_class=RedirectResponse)
async def remove_user(request: Request, user_id: int):
    db.delete_user(user_id)
    return RedirectResponse(url=request.url_for("get_users"), status_code=303)

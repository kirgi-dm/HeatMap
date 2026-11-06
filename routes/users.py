from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from database.connection import db
from dependencies import templates
from models.users import User, UserCreate, UserUpdate

user_router = APIRouter(tags=["Пользователи"])


@user_router.get("/users", response_class=HTMLResponse)
async def get_users(request: Request):
    return templates.TemplateResponse(
        request=request, name="users.html", context={"users": await db.list_users()}
    )


@user_router.post("/user", response_class=RedirectResponse)
async def create_user(request: Request, user: UserCreate = Depends(UserCreate.as_form)):
    await db.create_user(user)
    return RedirectResponse(url=request.url_for("get_users"), status_code=303)


@user_router.get("/user/{user_id}", response_class=HTMLResponse)
async def get_user(request: Request, user_id: PydanticObjectId, edit: bool = False):
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={"user": await db.get_user(user_id), "editing": edit},
    )


@user_router.put("/user/{user_id}", response_model=User, response_model_by_alias=False)
async def update_user(user_id: PydanticObjectId, user: UserUpdate):
    return await db.update_user(user_id, user)


@user_router.delete("/user/{user_id}", response_model=User, response_model_by_alias=False)
async def delete_user(user_id: PydanticObjectId):
    return await db.delete_user(user_id)


@user_router.post("/user/{user_id}/edit", response_class=RedirectResponse)
async def save_user(
    request: Request, user_id: PydanticObjectId, user: UserCreate = Depends(UserCreate.as_form)
):
    await db.update_user(user_id, user)
    return RedirectResponse(url=request.url_for("get_users"), status_code=303)


@user_router.post("/user/{user_id}/delete", response_class=RedirectResponse)
async def remove_user(request: Request, user_id: PydanticObjectId):
    await db.delete_user(user_id)
    return RedirectResponse(url=request.url_for("get_users"), status_code=303)


@user_router.get("/api/users", response_model=list[User], response_model_by_alias=False)
async def list_users_api():
    return await db.list_users()


@user_router.get("/api/users/{user_id}", response_model=User, response_model_by_alias=False)
async def get_user_api(user_id: PydanticObjectId):
    return await db.get_user(user_id)


@user_router.post("/api/users", response_model=User, response_model_by_alias=False, status_code=201)
async def create_user_api(body: UserCreate):
    return await db.create_user(body)

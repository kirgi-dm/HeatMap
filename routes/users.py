from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from database.connection import Database, get_database
from dependencies import templates
from models.users import User, UserCreate

user_router = APIRouter(tags=["Пользователи"])


@user_router.get("/users", response_class=HTMLResponse)
def get_users(request: Request, db: Database = Depends(get_database)):
    return templates.TemplateResponse(
        request=request, name="users.html", context={"users": db.list_users()}
    )


@user_router.post("/user", response_class=RedirectResponse)
def create_user(
    request: Request,
    user: UserCreate = Depends(UserCreate.as_form),
    db: Database = Depends(get_database),
):
    db.create_user(user)
    return RedirectResponse(url=request.url_for("get_users"), status_code=303)


@user_router.get("/user/{user_id}", response_class=HTMLResponse)
def get_user(
    request: Request, user_id: int, edit: bool = False,
    db: Database = Depends(get_database),
):
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={"user": db.get_user(user_id), "editing": edit},
    )


@user_router.put("/user/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate, db: Database = Depends(get_database)):
    return db.update_user(user_id, user)


@user_router.delete("/user/{user_id}", response_model=User)
def delete_user(user_id: int, db: Database = Depends(get_database)):
    return db.delete_user(user_id)


@user_router.post("/user/{user_id}/edit", response_class=RedirectResponse)
def save_user(
    request: Request, user_id: int, user: UserCreate = Depends(UserCreate.as_form),
    db: Database = Depends(get_database),
):
    db.update_user(user_id, user)
    return RedirectResponse(url=request.url_for("get_users"), status_code=303)


@user_router.post("/user/{user_id}/delete", response_class=RedirectResponse)
def remove_user(request: Request, user_id: int, db: Database = Depends(get_database)):
    db.delete_user(user_id)
    return RedirectResponse(url=request.url_for("get_users"), status_code=303)

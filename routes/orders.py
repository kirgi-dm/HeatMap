from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from database.connection import Database, get_database
from dependencies import templates
from models.orders import Order, OrderCreate

order_router = APIRouter(tags=["Заказы"])


def order_context(db: Database):
    users = db.list_users()
    return {"users": users, "users_by_id": {user.id: user for user in users}}


@order_router.get("/order", response_class=HTMLResponse)
def get_orders(request: Request, db: Database = Depends(get_database)):
    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={**order_context(db), "orders": db.list_orders()},
    )


@order_router.post("/order", response_class=RedirectResponse)
def create_order(
    request: Request,
    order: OrderCreate = Depends(OrderCreate.as_form),
    db: Database = Depends(get_database),
):
    db.create_order(order)
    return RedirectResponse(url=request.url_for("get_orders"), status_code=303)


@order_router.get("/order/{order_id}", response_class=HTMLResponse)
def get_order(
    request: Request, order_id: int, edit: bool = False,
    db: Database = Depends(get_database),
):
    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={**order_context(db), "order": db.get_order(order_id), "editing": edit},
    )


@order_router.put("/order/{order_id}", response_model=Order)
def update_order(order_id: int, order: OrderCreate, db: Database = Depends(get_database)):
    return db.update_order(order_id, order)


@order_router.delete("/order/{order_id}", response_model=Order)
def delete_order(order_id: int, db: Database = Depends(get_database)):
    return db.delete_order(order_id)


@order_router.post("/order/{order_id}/edit", response_class=RedirectResponse)
def save_order(
    request: Request, order_id: int, order: OrderCreate = Depends(OrderCreate.as_form),
    db: Database = Depends(get_database),
):
    db.update_order(order_id, order)
    return RedirectResponse(url=request.url_for("get_orders"), status_code=303)


@order_router.post("/order/{order_id}/delete", response_class=RedirectResponse)
def remove_order(request: Request, order_id: int, db: Database = Depends(get_database)):
    db.delete_order(order_id)
    return RedirectResponse(url=request.url_for("get_orders"), status_code=303)

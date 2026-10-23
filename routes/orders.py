from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from database.connection import db
from dependencies import templates
from models.orders import Order, OrderCreate

order_router = APIRouter(tags=["Заказы"])


def order_context():
    return {"users": list(db.users.values()), "users_by_id": db.users}


@order_router.get("/order", response_class=HTMLResponse)
async def get_orders(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={**order_context(), "orders": list(db.orders.values())},
    )


@order_router.post("/order", response_class=RedirectResponse)
async def create_order(request: Request, order: OrderCreate = Depends(OrderCreate.as_form)):
    db.create_order(order)
    return RedirectResponse(url=request.url_for("get_orders"), status_code=303)


@order_router.get("/order/{order_id}", response_class=HTMLResponse)
async def get_order(request: Request, order_id: int, edit: bool = False):
    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={**order_context(), "order": db.get_order(order_id), "editing": edit},
    )


@order_router.put("/order/{order_id}", response_model=Order)
async def update_order(order_id: int, order: OrderCreate):
    return db.update_order(order_id, order)


@order_router.delete("/order/{order_id}", response_model=Order)
async def delete_order(order_id: int):
    return db.delete_order(order_id)


@order_router.post("/order/{order_id}/edit", response_class=RedirectResponse)
async def save_order(
    request: Request, order_id: int, order: OrderCreate = Depends(OrderCreate.as_form)
):
    db.update_order(order_id, order)
    return RedirectResponse(url=request.url_for("get_orders"), status_code=303)


@order_router.post("/order/{order_id}/delete", response_class=RedirectResponse)
async def remove_order(request: Request, order_id: int):
    db.delete_order(order_id)
    return RedirectResponse(url=request.url_for("get_orders"), status_code=303)

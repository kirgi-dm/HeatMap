from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from database.connection import db
from dependencies import templates
from models.orders import Order, OrderCreate, OrderUpdate

order_router = APIRouter(tags=["Заказы"])


async def order_context():
    users = await db.list_users()
    return {"users": users, "users_by_id": {user.id: user for user in users}}


@order_router.get("/order", response_class=HTMLResponse)
async def get_orders(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={**(await order_context()), "orders": await db.list_orders()},
    )


@order_router.post("/order", response_class=RedirectResponse)
async def create_order(request: Request, order: OrderCreate = Depends(OrderCreate.as_form)):
    await db.create_order(order)
    return RedirectResponse(url=request.url_for("get_orders"), status_code=303)


@order_router.get("/order/{order_id}", response_class=HTMLResponse)
async def get_order(request: Request, order_id: PydanticObjectId, edit: bool = False):
    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={**(await order_context()), "order": await db.get_order(order_id), "editing": edit},
    )


@order_router.put("/order/{order_id}", response_model=Order, response_model_by_alias=False)
async def update_order(order_id: PydanticObjectId, order: OrderUpdate):
    return await db.update_order(order_id, order)


@order_router.delete("/order/{order_id}", response_model=Order, response_model_by_alias=False)
async def delete_order(order_id: PydanticObjectId):
    return await db.delete_order(order_id)


@order_router.post("/order/{order_id}/edit", response_class=RedirectResponse)
async def save_order(
    request: Request, order_id: PydanticObjectId, order: OrderCreate = Depends(OrderCreate.as_form)
):
    await db.update_order(order_id, order)
    return RedirectResponse(url=request.url_for("get_orders"), status_code=303)


@order_router.post("/order/{order_id}/delete", response_class=RedirectResponse)
async def remove_order(request: Request, order_id: PydanticObjectId):
    await db.delete_order(order_id)
    return RedirectResponse(url=request.url_for("get_orders"), status_code=303)


@order_router.get("/api/orders", response_model=list[Order], response_model_by_alias=False)
async def list_orders_api():
    return await db.list_orders()


@order_router.get("/api/orders/{order_id}", response_model=Order, response_model_by_alias=False)
async def get_order_api(order_id: PydanticObjectId):
    return await db.get_order(order_id)


@order_router.post("/api/orders", response_model=Order, response_model_by_alias=False, status_code=201)
async def create_order_api(body: OrderCreate):
    return await db.create_order(body)

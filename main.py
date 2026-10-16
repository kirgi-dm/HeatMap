from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from schemas import User, Order

app = FastAPI()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

user_list = []
order_list = []

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")


@app.post('/user', response_class=HTMLResponse)
async def create_user(request: Request, user: User = Depends(User.as_form)):
    user_list.append(user.dict())
    return templates.TemplateResponse(
        request=request, name="users.html", context={"users": user_list}
    )


@app.post('/order', response_class=HTMLResponse)
async def create_order(request: Request, order: Order = Depends(Order.as_form)):
    order_list.append(order.dict())
    return templates.TemplateResponse(
        request=request, name="orders.html", context={"orders": order_list}
    )


@app.get('/users', response_class=HTMLResponse)
async def get_users(request: Request):
    return templates.TemplateResponse(
        request=request, name="users.html", context={"users": user_list}
    )

@app.get('/order', response_class=HTMLResponse)
async def get_orders(request: Request, name: str | None = None, edit: bool = False):
    if name is not None:
        for order in order_list:
            if order['name'] == name:
                return templates.TemplateResponse(
                    request=request, name="orders.html",
                    context={"order": order, "editing": edit}
                )
        raise HTTPException(status_code=404, detail="Order not found")
    return templates.TemplateResponse(
        request=request, name="orders.html", context={"orders": order_list}
    )

@app.get('/user', response_class=HTMLResponse)
async def get_user(request: Request, username: str, edit: bool = False):
    for user in user_list:
        if user['username'] == username:
            return templates.TemplateResponse(
                request=request, name="users.html",
                context={"user": user, "editing": edit}
            )
    raise HTTPException(status_code=404, detail="User not found")


@app.put('/user')
async def update_user(username: str, user: User):
    for current_user in user_list:
        if current_user['username'] == username:
            current_user.update(user.dict())
            return {"user": current_user}
    return {'error': 'User not found'}


@app.delete('/user')
async def delete_user(username: str):
    for user in user_list:
        if user['username'] == username:
            user_list.remove(user)
            return {"user": user}
    return {'error': 'User not found'}


@app.put('/order')
async def update_order(name: str, order: Order):
    for current_order in order_list:
        if current_order['name'] == name:
            current_order.update(order.dict())
            return {"order": current_order}
    return {'error': 'Order not found'}


@app.delete('/order')
async def delete_order(name: str):
    for order in order_list:
        if order['name'] == name:
            order_list.remove(order)
            return {"order": order}
    return {'error': 'Order not found'}


@app.post('/user/edit', response_class=RedirectResponse)
async def save_user(request: Request, username: str, user: User = Depends(User.as_form)):
    result = await update_user(username, user)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return RedirectResponse(url=request.url_for('get_users'), status_code=303)


@app.post('/user/delete', response_class=RedirectResponse)
async def remove_user(request: Request, username: str):
    result = await delete_user(username)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return RedirectResponse(url=request.url_for('get_users'), status_code=303)


@app.post('/order/edit', response_class=RedirectResponse)
async def save_order(request: Request, name: str, order: Order = Depends(Order.as_form)):
    result = await update_order(name, order)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return RedirectResponse(url=request.url_for('get_orders'), status_code=303)


@app.post('/order/delete', response_class=RedirectResponse)
async def remove_order(request: Request, name: str):
    result = await delete_order(name)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return RedirectResponse(url=request.url_for('get_orders'), status_code=303)

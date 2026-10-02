from fastapi import FastAPI
from schemas import User, Order

app = FastAPI()

user_list = []
order_list = []

@app.get("/")
async def root():
    return {"message": "Приветствую, Дмитрий"}


@app.post('/user')
async def create_user(user: User):
    user_list.append(user.dict())
    return {"user": user.dict()}


@app.post('/order')
async def create_order(order: Order):
    order_list.append(order.dict())
    return {"order": order.dict()}


@app.get('/users')
async def get_users():
    return {"user": user_list}

@app.get('/order')
async def get_orders():
    return {"order": order_list}

@app.get('/user')
async def get_user(username: str):
    for user in user_list:
        if user['username'] == username:
            return {"user": user}
    return {'error': 'User not found'}
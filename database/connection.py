"""Учебное хранилище в памяти. Данные существуют до перезапуска приложения."""

from itertools import count

from models import Order, OrderCreate, User, UserCreate


class StorageError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class MemoryDatabase:
    def __init__(self):
        self.users: dict[int, User] = {}
        self.orders: dict[int, Order] = {}
        self._user_ids = count(1)
        self._order_ids = count(1)

    def get_user(self, user_id: int) -> User:
        if user_id not in self.users:
            raise StorageError("Пользователь не найден", 404)
        return self.users[user_id]

    def get_order(self, order_id: int) -> Order:
        if order_id not in self.orders:
            raise StorageError("Заказ не найден", 404)
        return self.orders[order_id]

    def create_user(self, data: UserCreate) -> User:
        user = User(id=next(self._user_ids), **data.model_dump())
        self.users[user.id] = user
        return user

    def update_user(self, user_id: int, data: UserCreate) -> User:
        self.get_user(user_id)
        user = User(id=user_id, **data.model_dump())
        self.users[user_id] = user
        return user

    def delete_user(self, user_id: int) -> User:
        self.get_user(user_id)
        if any(order.user_id == user_id for order in self.orders.values()):
            raise StorageError(
                "У пользователя есть заказы. Сначала удалите их или назначьте другому пользователю.",
                409,
            )
        return self.users.pop(user_id)

    def create_order(self, data: OrderCreate) -> Order:
        self.get_user(data.user_id)
        order = Order(id=next(self._order_ids), **data.model_dump())
        self.orders[order.id] = order
        return order

    def update_order(self, order_id: int, data: OrderCreate) -> Order:
        self.get_order(order_id)
        self.get_user(data.user_id)
        order = Order(id=order_id, **data.model_dump())
        self.orders[order_id] = order
        return order

    def delete_order(self, order_id: int) -> Order:
        self.get_order(order_id)
        return self.orders.pop(order_id)


db = MemoryDatabase()

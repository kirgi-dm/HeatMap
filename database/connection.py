import os
from pathlib import Path

from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select

from models import Order, OrderCreate, User, UserCreate
from models.orders import OrderTable
from models.users import UserTable

DATABASE_PATH = Path(
    os.environ.get("HEATMAP_DB_PATH", Path(__file__).resolve().parents[1] / "heatmap.db")
).expanduser().resolve()


def create_sqlite_engine(path: Path):
    engine = create_engine(
        f"sqlite:///{path}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = create_sqlite_engine(DATABASE_PATH)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


class StorageError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class Database:
    def __init__(self, session: Session):
        self.session = session

    def _commit(self):
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise StorageError(
                "Операция нарушает связь пользователя и заказа. Обновите данные.", 409
            ) from error

    def _user_row(self, user_id: int) -> UserTable:
        user = self.session.get(UserTable, user_id)
        if user is None:
            raise StorageError("Пользователь не найден", 404)
        return user

    def _order_row(self, order_id: int) -> OrderTable:
        order = self.session.get(OrderTable, order_id)
        if order is None:
            raise StorageError("Заказ не найден", 404)
        return order

    def list_users(self) -> list[User]:
        rows = self.session.exec(select(UserTable).order_by(UserTable.id)).all()
        return [User.model_validate(row, from_attributes=True) for row in rows]

    def list_orders(self) -> list[Order]:
        rows = self.session.exec(select(OrderTable).order_by(OrderTable.id)).all()
        return [Order.model_validate(row, from_attributes=True) for row in rows]

    def get_user(self, user_id: int) -> User:
        return User.model_validate(self._user_row(user_id), from_attributes=True)

    def get_order(self, order_id: int) -> Order:
        return Order.model_validate(self._order_row(order_id), from_attributes=True)

    def create_user(self, data: UserCreate) -> User:
        user = UserTable(**data.model_dump())
        self.session.add(user)
        self._commit()
        self.session.refresh(user)
        return User.model_validate(user, from_attributes=True)

    def update_user(self, user_id: int, data: UserCreate) -> User:
        user = self._user_row(user_id)
        user.username = data.username
        user.email = str(data.email)
        self.session.add(user)
        self._commit()
        self.session.refresh(user)
        return User.model_validate(user, from_attributes=True)

    def delete_user(self, user_id: int) -> User:
        user = self._user_row(user_id)
        order = self.session.exec(
            select(OrderTable).where(OrderTable.user_id == user_id).limit(1)
        ).first()
        if order is not None:
            raise StorageError(
                "У пользователя есть заказы. Сначала удалите их или назначьте другому пользователю.",
                409,
            )
        result = User.model_validate(user, from_attributes=True)
        self.session.delete(user)
        self._commit()
        return result

    def create_order(self, data: OrderCreate) -> Order:
        self._user_row(data.user_id)
        order = OrderTable(**data.model_dump())
        self.session.add(order)
        self._commit()
        self.session.refresh(order)
        return Order.model_validate(order, from_attributes=True)

    def update_order(self, order_id: int, data: OrderCreate) -> Order:
        order = self._order_row(order_id)
        self._user_row(data.user_id)
        order.name = data.name
        order.user_id = data.user_id
        self.session.add(order)
        self._commit()
        self.session.refresh(order)
        return Order.model_validate(order, from_attributes=True)

    def delete_order(self, order_id: int) -> Order:
        order = self._order_row(order_id)
        result = Order.model_validate(order, from_attributes=True)
        self.session.delete(order)
        self._commit()
        return result


def get_database(session: Session = Depends(get_session)) -> Database:
    return Database(session)

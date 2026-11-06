# HeatMap

Учебное приложение FastAPI для управления пользователями и заказами.
Практическая работа №9: подключение нереляционной базы MongoDB через Beanie.
Ветка alternative-db основана на a639e30, до внедрения SQLite.

## Запуск

Из каталога проекта:

~~~bash
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
~~~

В .env задаётся DATABASE_URL=mongodb://localhost:27017/heatmap.
Имя базы в конце URI обязательно. Переменная окружения имеет приоритет над .env.
При старте приложения Beanie инициализирует коллекции и индекс orders.user_id.
При завершении приложения соединение закрывается.

Запустите установленный сервер MongoDB в отдельном терминале:

~~~bash
mkdir -p store
mongod --dbpath store --bind_ip 127.0.0.1 --port 27017
~~~

Если MongoDB установлена через системный сервис, достаточно запустить этот сервис.
Альтернатива для компьютера с доступным Docker:

~~~bash
docker compose up -d
~~~

После этого запустите приложение во втором терминале:

~~~bash
source .venv/bin/activate
python main.py
~~~

Главная: http://127.0.0.1:8000/ · Пользователи: http://127.0.0.1:8000/users
· Заказы: http://127.0.0.1:8000/order · Swagger: http://127.0.0.1:8000/docs

Если MongoDB недоступна, запуск приложения завершится ошибкой подключения
примерно через 5 секунд. Приложение не подменяет БД хранилищем в памяти.

## Структура

- main.py: FastAPI, lifespan подключения и закрытия MongoDB, обработка ошибок.
- database/connection.py: Settings, универсальный Database(model) и правила HeatMapDatabase.
- models/users.py: UserCreate, UserUpdate и документ User (коллекция users).
- models/orders.py: OrderCreate, OrderUpdate и документ Order (коллекция orders).
- routes/: асинхронные маршруты для HTML, форм и JSON.
- templates/: формы, списки, карточки, ошибки.
- docs/practice9.md: структура БД, команды curl и mongosh, сценарии.
- docs/use_cases.puml: UML use case в формате PlantUML.
- docs/workflows.bpmn: BPMN 2.0 для сохранения, просмотра и удаления пользователей и заказов.
- tests/test_app.py: интеграционные проверки с настоящей MongoDB.

## Данные

User: MongoDB _id, username, email. Order: _id, name, user_id.
Идентификаторы назначаются MongoDB автоматически и передаются в JSON как строки id.
В MongoDB связь orders.user_id хранится как ObjectId; на неё создан индекс.
При перезапуске приложения данные и идентификаторы сохраняются.
Локальный файл heatmap.db принадлежит версии с SQLite; эта ветка его не использует.

Совпадающие имена и email разрешены, как в исходной версии проекта.
Заказ требует существующего пользователя (иначе 404).
Пользователя с заказами удалить нельзя (409): сначала удалите заказы или
переназначьте их другому пользователю. MongoDB не обеспечивает внешние ключи;
эти проверки выполняются приложением отдельными запросами и не являются
транзакционной гарантией при конкурентных изменениях или прямых записях в БД.

## Маршруты

| Метод | Путь | Назначение |
|---|---|---|
| GET | / | Главная |
| GET | /users | HTML-список и форма пользователя |
| POST | /user | Создание пользователя из формы |
| GET | /user/{user_id} | Карточка; ?edit=true открывает редактирование |
| PUT | /user/{user_id} | Частичное обновление, JSON |
| DELETE | /user/{user_id} | Удаление, ответ JSON |
| POST | /user/{user_id}/edit | Сохранение формы |
| POST | /user/{user_id}/delete | Удаление из браузера |
| GET | /order | HTML-список и форма заказа |
| POST | /order | Создание заказа из формы |
| GET | /order/{order_id} | Карточка; ?edit=true открывает редактирование |
| PUT | /order/{order_id} | Частичное обновление, JSON |
| DELETE | /order/{order_id} | Удаление, ответ JSON |
| POST | /order/{order_id}/edit | Сохранение формы |
| POST | /order/{order_id}/delete | Удаление из браузера |
| GET, POST | /api/users | JSON-список / создание пользователя |
| GET | /api/users/{user_id} | Пользователь в JSON |
| GET, POST | /api/orders | JSON-список / создание заказа |
| GET | /api/orders/{order_id} | Заказ в JSON |

Формы перенаправляют на список (303), JSON-создание возвращает запись (201).
PUT возвращает обновлённую запись, DELETE - удалённую (200).
Обновляются только переданные непустые поля; null игнорируется по методичке.
Невалидный ObjectId или тело запроса дают 422, отсутствующая запись - 404.
Все операции с БД асинхронные, через Beanie.

## Проверка

Используйте отдельный сервер или тот же локальный MongoDB:

~~~bash
HEATMAP_TEST_MONGODB_URL=mongodb://localhost:27017 python -m unittest discover -s tests -v
~~~

Каждый тест создаёт уникальную БД heatmap_test_<uuid> и удаляет только её.
Без HEATMAP_TEST_MONGODB_URL тесты пропускаются.
Проверены 7 сценариев на MongoDB 8.0.16: CRUD и связь владельца,
HTML и формы, 404/409/422, сохранение после перезапуска приложения,
частичные обновления, совпадающие имена, BSON-ссылка и индекс.

## Адаптация методички

Сохранена предметная область проекта: пользователи и заказы. Пример регистрации
и входа из планировщика событий не переносится в управление пользователями.
Методы Database(model): save, get, get_all, update, delete.
BaseSettings импортируется из pydantic-settings (Pydantic 2).
Beanie 2 использует AsyncMongoClient из PyMongo вместо Motor:
https://beanie-odm.dev/tutorial/initialization/.

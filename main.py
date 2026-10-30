from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from database.connection import StorageError, create_db_and_tables
from dependencies import templates
from routes.orders import order_router
from routes.pages import page_router
from routes.users import user_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="HeatMap", description="Управление пользователями и заказами", lifespan=lifespan
)


@app.exception_handler(StorageError)
async def storage_error_handler(request: Request, error: StorageError):
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": str(error), "status_code": error.status_code},
            status_code=error.status_code,
        )
    return JSONResponse(status_code=error.status_code, content={"detail": str(error)})


app.include_router(page_router)
app.include_router(user_router)
app.include_router(order_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

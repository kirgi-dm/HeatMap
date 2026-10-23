from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from dependencies import templates

page_router = APIRouter(tags=["Страницы"])


@page_router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")

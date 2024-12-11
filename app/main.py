"""
Основной файл приложения FastAPI.

Содержит:
- Настройку жизненного цикла приложения (подключение и отключение БД).
- Подключение маршрутов (эндпоинтов) для работы с API.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.connection import db
from app.repositories.routers import router as repos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Настройка жизненного цикла приложения.

    Включает:
    - Подключение к базе данных при старте приложения.
    - Отключение от базы данных при завершении работы.
    """
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(lifespan=lifespan)

app.include_router(repos_router)

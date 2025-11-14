# Главный файл приложения
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import init_db, get_async_session
from routers import tasks, stats

@asynccontextmanager
async def lifespan():
    print("Запуск приложения...")
    print("Инициализация базы данных...")
    await init_db()
    print("Приложение готово к работе")
    yield
    print("Остановка приложения...")

app = FastAPI(
    title="ToDo лист API",
    description="API для управления задачами с использованием матрицы Эйзенхауэра",
    version="2.0.0",
    contact={
        "name": "Гладышев Николай",
    }
)

app.include_router(tasks.router, prefix="/api/v2")
app.include_router(stats.router, prefix="/api/v2")

@app.get("/")
async def welcome() -> dict:
    return {
        "message": "Привет, студент!",
        "api_title": app.title,
        "api_description": app.description,
        "api_version": app.version,
        "api_author": app.contact["name"],
    }

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_async_session)) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "database": db_status,
    }

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from models import Task
from routers.tasks import valid_quadrants

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
)

@router.get("/")
async def get_tasks_stats(db: AsyncSession = Depends(get_async_session)) -> dict:
    result = await db.execute(select(Task))
    tasks = result.scalars().all()

    def count_by(predicate) -> int:
        count = 0
        for task in tasks:
            if predicate(task):
                count += 1
        return count

    return {
        "total_tasks": len(tasks),
        "by_quadrant": { quadrant: count_by(lambda x: x.quadrant == quadrant) for quadrant in valid_quadrants },
        "by_status": {
            "completed": count_by(lambda task: task.completed),
            "pending": count_by(lambda task: not task.completed),
        },
    }

@router.get("/deadlines")
async def get_deadlines(db: AsyncSession = Depends(get_async_session)) -> list:
    result = await db.execute(select(Task).where((Task.completed == False) & (Task.deadline_at != None)))
    tasks = result.scalars().all()

    response_data = []
    for task in tasks:
        response_data.append({
            "title": task.title,
            "description": task.description,
            "deadline_at": task.deadline_at,
            "delta": (task.deadline_at - datetime.now()).days,
        })

    return response_data

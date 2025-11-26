from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from models import Task
from routers.tasks import valid_quadrants
from schemas import TimingStatsResponse

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

@router.get("/deadlines", response_model=TimingStatsResponse)
async def get_deadlines(db: AsyncSession = Depends(get_async_session)) -> TimingStatsResponse:
    now_utc = datetime.now(timezone.utc)

    statement = select(
        func.sum(
            case(((Task.completed == True) & (Task.completed_at <= Task.deadline_at), 1), else_=0)
        ).label("completed_on_time"),
        func.sum(
            case(((Task.completed == True) & (Task.completed_at > Task.deadline_at), 1), else_=0)
        ).label("completed_late"),
        func.sum(
            case(((Task.completed == False) & (Task.deadline_at != None) & (Task.deadline_at > now_utc), 1), else_=0)
        ).label("on_plan_pending"),
        func.sum(
            case(((Task.completed == False) & (Task.deadline_at != None) & (Task.deadline_at <= now_utc), 1), else_=0)
        ).label("overdue_pending"),
    ).select_from(Task)

    result = await db.execute(statement)
    stats_row = result.one()

    return TimingStatsResponse(
        completed_on_time=stats_row.completed_on_time or 0,
        completed_late=stats_row.completed_late or 0,
        on_plan_pending=stats_row.on_plan_pending or 0,
        overtime_pending=stats_row.overdue_pending or 0,
    )

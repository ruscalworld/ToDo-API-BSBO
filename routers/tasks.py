import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi import Response
from sqlalchemy import select, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database import get_async_session
from models import Task
from schemas import TaskCreate, TaskResponse, TaskUpdate

valid_quadrants = ["Q1", "Q2", "Q3", "Q4"]
valid_statuses = ["completed", "pending"]

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Task not found"}},
)

def get_quadrant(is_important: bool, is_urgent: bool) -> str:
    if is_important and is_urgent:
        return "Q1"
    elif is_important and not is_urgent:
        return "Q2"
    elif not is_important and is_urgent:
        return "Q3"
    else:
        return "Q4"

def get_urgent(deadline_at: datetime.datetime) -> bool:
    diff = deadline_at - datetime.datetime.now(tz=deadline_at.tzinfo)
    return diff < datetime.timedelta(days=3)

@router.get("/", response_model=List[TaskResponse])
async def get_all_tasks(db: AsyncSession = Depends(get_async_session)) -> Sequence[Task]:
    result = await db.execute(select(Task))
    tasks = result.scalars().all()
    return tasks

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TaskResponse)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_async_session)) -> Task:
    new_task = Task(
        title=task.title,
        description=task.description,
        is_important=task.is_important,
        is_urgent=get_urgent(task.deadline_at),
        quadrant=get_quadrant(task.is_important, get_urgent(task.deadline_at)),
        completed=False,
        deadline_at=task.deadline_at,
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task

@router.get("/quadrant/{quadrant}", response_model=List[TaskResponse])
async def get_tasks_by_quadrant(quadrant: str, db: AsyncSession = Depends(get_async_session)) -> Sequence[Task]:
    if quadrant not in valid_quadrants:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный квадрант. Используйте: {', '.join(valid_quadrants)}",
        )

    result = await db.execute(select(Task).where(Task.quadrant == quadrant))
    tasks = result.scalars().all()

    return tasks

@router.get("/search", response_model=List[TaskResponse])
async def search_tasks(q: str, db: AsyncSession = Depends(get_async_session)) -> Sequence[Task]:
    if len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="Ключевое слово должно быть длиннее 2 символов."
        )

    keyword = f'%{q.lower()}%'
    result = await db.execute(select(Task).where(
        (Task.title.ilike(keyword)) | ((Task.description.ilike(keyword)))
    ))
    tasks = result.scalars().all()

    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(task_id: str, db: AsyncSession = Depends(get_async_session)) -> Task:
    if not task_id.isdigit():
        raise HTTPException(
            status_code=422,
            detail="Некорректный ID."
        )

    result = await db.execute(select(Task).where(Task.id == int(task_id)))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Задача с ID {task_id} не найдена."
        )

    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate, db: AsyncSession = Depends(get_async_session)) -> Task:
    result = await db.execute(select(Task).where(Task.id == int(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    if "is_important" in update_data or "deadline" in update_data:
        task.is_urgent = get_urgent(update_data["deadline_at"])
        task.quadrant = get_quadrant(task.is_important, task.is_urgent)

    await db.commit()
    await db.refresh(task)

    return task

@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: int, db: AsyncSession = Depends(get_async_session)) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    task.completed = True
    task.completed_at = datetime.now()

    await db.commit()
    await db.refresh(task)

    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    await db.delete(task)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/status/{status}", response_model=List[TaskResponse])
async def get_tasks_by_status(status: str, db: AsyncSession = Depends(get_async_session)) -> Sequence[Task]:
    if status not in valid_statuses:
        raise HTTPException(
            status_code=404,
            detail=f"Неверный статус. Используйте: {', '.join(valid_statuses)}",
        )

    is_completed = (status == "completed")
    result = await db.execute(select(Task).where(Task.completed == is_completed))
    tasks = result.scalars().all()

    return tasks

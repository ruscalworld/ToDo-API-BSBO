import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi import Response
from sqlalchemy import select, Sequence, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database import get_async_session
from dependencies import get_current_user
from models import Task, User, UserRole
from schemas import TaskCreate, TaskResponse, TaskUpdate

valid_quadrants = ["Q1", "Q2", "Q3", "Q4"]
valid_statuses = ["completed", "pending"]

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Task not found"}},
)

@router.get("/", response_model=List[TaskResponse])
async def get_all_tasks(db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)) -> Sequence[Task]:
    if current_user.role == UserRole.ADMIN.value:
        result = await db.execute(select(Task))
    else:
        result = await db.execute(select(Task).where(Task.user_id == current_user.id))

    return result.scalars().all()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TaskResponse)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)) -> Task:
    new_task = Task(
        title=task.title,
        description=task.description,
        is_important=task.is_important,
        completed=False,
        user_id=current_user.id,
        deadline_at=task.deadline_at,
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task

@router.get("/quadrant/{quadrant}", response_model=List[TaskResponse])
async def get_tasks_by_quadrant(quadrant: str, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)) -> List[Task]:
    if quadrant not in valid_quadrants:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный квадрант. Используйте: {', '.join(valid_quadrants)}",
        )

    if current_user.role == UserRole.ADMIN.value:
        result = await db.execute(select(Task))
    else:
        result = await db.execute(select(Task).where(Task.user_id == current_user.id))
    all_tasks = result.scalars().all()

    return [task for task in all_tasks if task.quadrant == quadrant]

@router.get("/search", response_model=List[TaskResponse])
async def search_tasks(q: str, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)) -> Sequence[Task]:
    if len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="Ключевое слово должно быть длиннее 2 символов."
        )

    keyword = f'%{q.lower()}%'
    if current_user.role == UserRole.ADMIN.value:
        result = await db.execute(select(Task).where(
            (Task.title.ilike(keyword)) | (Task.description.ilike(keyword))
        ))
    else:
        result = await db.execute(select(Task).where(
            ((Task.title.ilike(keyword)) | (Task.description.ilike(keyword))) & (Task.user_id == current_user.id)
        ))
    tasks = result.scalars().all()

    return tasks

@router.get("/today", response_model=List[TaskResponse])
async def get_today_tasks(db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)) -> Sequence[Task]:
    today = datetime.date.today()
    if current_user.role == UserRole.ADMIN.value:
        result = await db.execute(select(Task).where(
            (Task.deadline_at != None) & (func.date(Task.deadline_at) == today)
        ))
    else:
        result = await db.execute(select(Task).where(
            ((Task.deadline_at != None) & (func.date(Task.deadline_at) == today)) & (Task.user_id == current_user.id)
        ))

    return result.scalars().all()

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(task_id: str, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)) -> Task:
    return await get_task(task_id, db, current_user)

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskUpdate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)) -> Task:
    task = await get_task(task_id, db, current_user)

    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    return task

@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: str, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)) -> Task:
    task = await get_task(task_id, db, current_user)

    task.completed = True
    task.completed_at = datetime.datetime.now()

    await db.commit()
    await db.refresh(task)

    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    task = await get_task(task_id, db, current_user)

    await db.delete(task)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/status/{status}", response_model=List[TaskResponse])
async def get_tasks_by_status(status: str, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)) -> Sequence[Task]:
    if status not in valid_statuses:
        raise HTTPException(
            status_code=404,
            detail=f"Неверный статус. Используйте: {', '.join(valid_statuses)}",
        )

    is_completed = (status == "completed")

    if current_user.role == UserRole.ADMIN.value:
        result = await db.execute(select(Task).where(Task.completed == is_completed))
    else:
        result = await db.execute(select(Task).where(
            (Task.completed == is_completed) & (Task.user_id == current_user.id)
        ))

    return result.scalars().all()

async def get_task(task_id: str, db: AsyncSession, current_user: User):
    if not task_id.isdigit():
        raise HTTPException(
            status_code=422,
            detail="Некорректный ID."
        )

    if current_user.role == UserRole.ADMIN.value:
        result = await db.execute(select(Task).where(Task.id == int(task_id)))
    else:
        result = await db.execute(select(Task).where(
            (Task.id == int(task_id)) & (Task.user_id == current_user.id)
        ))

    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task

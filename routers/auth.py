from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_async_session
from models import User
from models.task import Task
from schemas_auth import UserResponse, UserWithTaskCount
from dependencies import get_current_user, get_current_admin

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@admin_router.get("/users", response_model=list[UserWithTaskCount])
async def get_all_users(_: User = Depends(get_current_admin), db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(
        select(User.id, User.external_id, User.role, func.count(Task.id).label("task_count"))
        .outerjoin(Task, User.id == Task.user_id)
        .group_by(User.id)
    )

    users = result.all()

    return [
        {
            "id": user.id,
            "external_id": user.external_id,
            "role": user.role,
            "task_count": user.task_count
        }
        for user in users
    ]

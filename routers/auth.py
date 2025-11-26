from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_async_session
from models import User, UserRole
from models.task import Task
from schemas_auth import UserCreate, UserResponse, Token, ChangePassword, UserWithTaskCount
from auth_utils import verify_password, get_password_hash, create_access_token
from dependencies import get_current_user, get_current_admin

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    result = await db.execute(
        select(User).where(User.nickname == user_data.nickname)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким никнеймом уже существует"
        )

    new_user = User(
        nickname=user_data.nickname,
        email=str(user_data.email),
        hashed_password=get_password_hash(user_data.password),
        role=UserRole.USER.value,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )

    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/change-password", status_code=status.HTTP_200_OK)
async def change_password(password_data: ChangePassword, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_session)):
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )

    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()

    return {"message": "Пароль успешно изменен"}


@admin_router.get("/users", response_model=list[UserWithTaskCount])
async def get_all_users(_: User = Depends(get_current_admin), db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(
        select(User.id, User.nickname, User.email, User.role, func.count(Task.id).label("task_count"))
        .outerjoin(Task, User.id == Task.user_id)
        .group_by(User.id)
    )

    users = result.all()

    return [
        {
            "id": user.id,
            "nickname": user.nickname,
            "email": user.email,
            "role": user.role,
            "task_count": user.task_count
        }
        for user in users
    ]

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_async_session
from models import User, UserRole
import os
from dotenv import load_dotenv

load_dotenv()

MANAGEMENT_KEY = os.getenv("MANAGEMENT_KEY")


async def verify_management_key(x_management_key: str = Header(..., alias="X-Management-Key")) -> None:
    if x_management_key != MANAGEMENT_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный ключ управления"
        )


async def get_current_user(
    x_user_id: str = Header(..., alias="X-User-Id"),
    db: AsyncSession = Depends(get_async_session),
    _: None = Depends(verify_management_key)
) -> User:
    result = await db.execute(
        select(User).where(User.external_id == x_user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            external_id=x_user_id,
            role=UserRole.USER.value,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )

    return current_user

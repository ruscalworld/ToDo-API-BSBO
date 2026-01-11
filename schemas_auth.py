from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    nickname: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Никнейм пользователя"
    )
    email: EmailStr = Field(
        ...,
        description="Email пользователя"
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Пароль (минимум 6 символов)"
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    nickname: str
    email: EmailStr
    role: str


class Config:
    from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None


class ChangePassword(BaseModel):
    old_password: str = Field(
        ...,
        description="Текущий пароль",
    )
    new_password: str = Field(
        ...,
        min_length=6,
        description="Новый пароль",
    )


class UserWithTaskCount(BaseModel):
    id: int
    nickname: str
    email: EmailStr
    role: str
    task_count: int

    class Config:
        from_attributes = True

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    external_id: str
    role: str

    class Config:
        from_attributes = True


class UserWithTaskCount(BaseModel):
    id: int
    external_id: str
    role: str
    task_count: int

    class Config:
        from_attributes = True

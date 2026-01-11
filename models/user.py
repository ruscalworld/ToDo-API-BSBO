from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base
import enum

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )
    external_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    role = Column(
        String(20),
        nullable=False,
        default=UserRole.USER.value,
    )

    tasks = relationship(
        "Task",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, external_id='{self.external_id}', role='{self.role}')>"

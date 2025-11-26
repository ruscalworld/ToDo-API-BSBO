import datetime

from pydantic import computed_field
from sqlalchemy import Column, Integer, Text, Boolean, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Task(Base):
    __tablename__ = "tasks"
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )
    title = Column(
        Text,
        nullable=False,
    )
    description = Column(
        Text,
        nullable=True,
    )
    is_important = Column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_urgent = Column(
        Boolean,
        nullable=False,
        default=False,
    )
    quadrant = Column(
        String(2),
        nullable=False,
    )
    completed = Column(
        Boolean,
        nullable=False,
        default=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    deadline_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner = relationship(
        "User",
        back_populates="tasks",
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', quadrant='{self.quadrant}')>"

    @computed_field
    @property
    def days_remaining(self):
        if self.deadline_at is None:
            return None

        return (self.deadline_at - datetime.datetime.now(tz=self.deadline_at.tzinfo)).days

    @computed_field
    @property
    def is_urgent(self):
        if self.days_remaining is None:
            return False
        return self.days_remaining <= 3

    @computed_field
    @property
    def quadrant(self):
        if self.is_important and self.is_urgent:
            return "Q1"
        elif self.is_important and not self.is_urgent:
            return "Q2"
        elif not self.is_important and self.is_urgent:
            return "Q3"
        else:
            return "Q4"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "is_important": self.is_important,
            "is_urgent": self.is_urgent,
            "quadrant": self.quadrant,
            "completed": self.completed,
            "created_at": self.created_at,
            "deadline_at": self.deadline_at,
            "completed_at": self.completed_at,
            "user_id": self.user_id,
        }

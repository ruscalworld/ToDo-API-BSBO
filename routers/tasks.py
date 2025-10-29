from datetime import datetime
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException

valid_quadrants = ["Q1", "Q2", "Q3", "Q4"]
valid_statuses = ["completed", "pending"]

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Task not found"}},
)

@router.get("/")
async def get_all_tasks() -> dict:
    return {
        "count": len(tasks_db),
        "tasks": tasks_db,
    }

@router.get("/quadrant/{quadrant}")
async def get_tasks_by_quadrant(quadrant: str) -> dict:
    if quadrant not in valid_quadrants:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный квадрант. Используйте: {', '.join(valid_quadrants)}",
        )

    filtered_tasks = [
        task
        for task in tasks_db
        if task["quadrant"] == quadrant
    ]

    return {
        "quadrant": quadrant,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks,
    }

@router.get("/stats")
async def get_tasks_stats() -> dict:
    def count_by(predicate) -> int:
        count = 0
        for task in tasks_db:
            if predicate(task):
                count += 1
        return count

    return {
        "total_tasks": len(tasks_db),
        "by_quadrant": { quadrant: count_by(lambda x: x["quadrant"] == quadrant) for quadrant in valid_quadrants },
        "by_status": {
            "completed": count_by(lambda task: task["completed"]),
            "pending": count_by(lambda task: not task["completed"]),
        },
    }

@router.get("/search")
async def search_tasks(q: str) -> dict:
    if len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="Ключевое слово должно быть длиннее 2 символов."
        )

    filtered_tasks = [
        task
        for task in tasks_db
        if task["title"] is not None and q in task["title"] or task["description"] is not None and q in task["description"]
    ]

    return {
        "query": q,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks,
    }

@router.get("/{task_id}")
async def get_task_by_id(task_id: str) -> dict:
    if not task_id.isdigit():
        raise HTTPException(
            status_code=422,
            detail="Некорректный ID."
        )

    for task in tasks_db:
        if task["id"] == int(task_id):
            return task
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Задача с ID {task_id} не найдена."
        )

@router.get("/status/{status}")
async def get_tasks_by_status(status: str) -> dict:
    if status not in valid_statuses:
        raise HTTPException(
            status_code=404,
            detail=f"Неверный статус. Используйте: {', '.join(valid_statuses)}",
        )

    filtered_tasks = [
        task
        for task in tasks_db
        if task["completed"] == (True if status == "completed" else False)
    ]

    return {
        "status": status,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks,
    }

# Временное хранилище (позже будет заменено на PostgreSQL)
tasks_db: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Сдать проект по FastAPI",
        "description": "Завершить разработку API и написать документацию",
        "is_important": True,
        "is_urgent": True,
        "quadrant": "Q1",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "title": "Изучить SQLAlchemy",
        "description": "Прочитать документацию и попробовать примеры",
        "is_important": True,
        "is_urgent": False,
        "quadrant": "Q2",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 3,
        "title": "Сходить на лекцию",
        "description": None,
        "is_important": False,
        "is_urgent": True,
        "quadrant": "Q3",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 4,
        "title": "Посмотреть сериал",
        "description": "Новый сезон любимого сериала",
        "is_important": False,
        "is_urgent": False,
        "quadrant": "Q4",
        "completed": True,
        "created_at": datetime.now()
    },
]

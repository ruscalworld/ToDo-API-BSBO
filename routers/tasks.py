from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi import Response
from starlette import status

from database import tasks_db
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

@router.get("/")
async def get_all_tasks() -> dict:
    return {
        "count": len(tasks_db),
        "tasks": tasks_db,
    }

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TaskResponse)
async def create_task(task: TaskCreate) -> TaskResponse:
    quadrant = get_quadrant(task.is_important, task.is_urgent)
    new_id = max([t["id"] for t in tasks_db], default=0) + 1

    new_task = {
        "id": new_id,
        "title": task.title,
        "description": task.description,
        "is_important": task.is_important,
        "is_urgent": task.is_urgent,
        "quadrant": quadrant,
        "completed": False,
        "created_at": datetime.now(),
    }

    tasks_db.append(new_task)

    return new_task

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

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(task_id: str) -> TaskResponse:
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

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate) -> TaskResponse:
    task = next((task for task in tasks_db if task["id"] == int(task_id)), None)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        task[field] = value

    if "is_important" in update_data or "is_urgent" in update_data:
        task["quadrant"] = get_quadrant(task["is_important"], task["is_urgent"])

    return task

@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: int) -> TaskResponse:
    task = next((task for task in tasks_db if task["id"] == int(task_id)), None)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    task["completed"] = True
    task["completed_at"] = datetime.now()

    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def complete_task(task_id: int):
    task = next((task for task in tasks_db if task["id"] == int(task_id)), None)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    tasks_db.remove(task)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

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

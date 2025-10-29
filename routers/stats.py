from fastapi import APIRouter

from database import tasks_db

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
)

@router.get("/")
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

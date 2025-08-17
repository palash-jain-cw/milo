from fastapi import APIRouter, Depends, HTTPException, Path
from milo.core.logger.logger_setup import loguru_setup
from milo.shared.dependencies import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from milo.task.models.orm import Task as TaskORM
from milo.task.models.schema import TaskCreate, TaskUpdate
import traceback
from uuid import UUID

logger = loguru_setup()

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal Server Error"},
        400: {"description": "Bad Request"},
    },
)


@router.post("/create")
async def add_task(task: TaskCreate, db: AsyncSession = Depends(get_db_session)):
    """
    Add a new task.
    """
    try:
        task = TaskORM(**task.model_dump())
        db.add(task)
        await db.commit()
        return task
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating task: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail="Failed to create task")


@router.put("/update")
async def update_task(task: TaskUpdate, db: AsyncSession = Depends(get_db_session)):
    """
    Update a task.
    """
    try:
        task = TaskORM(**task.model_dump())
        db.add(task)
        await db.commit()
        return task
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating task: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail="Failed to update task")


@router.get("/get")
async def get_task(
    task_id: UUID = Path(..., description="The UUID of the task to get"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get a task by ID.
    """
    try:
        task = await db.get(TaskORM, task_id)
        if not task:
            raise HTTPException(
                status_code=404, detail=f"Task with id {task_id} not found"
            )
        return task
    except Exception as e:
        logger.error(f"Error getting task: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="Internal server error while getting task"
        )

@router.delete("/delete", status_code=200)
async def delete_task(task_id: UUID, db: AsyncSession = Depends(get_db_session)):
    """
    Delete a task by ID.
    """
    try:
        task = await db.get(TaskORM, task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        await db.delete(task)
        await db.commit()
        return {"message": f"Task with id {task_id} deleted successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting task: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting task")
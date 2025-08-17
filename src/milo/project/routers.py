from fastapi import APIRouter, Depends, HTTPException, Path
from milo.core.logger.logger_setup import loguru_setup
from milo.shared.dependencies import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from milo.project.models.orm import Project as ProjectORM
from milo.project.models.schema import Project as ProjectSchema
from milo.project.models.dto import ProjectUpdate
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


@router.get("/list")
async def get_projects(db: AsyncSession = Depends(get_db_session)):
    """
    List all projects in the system.
    """
    try:
        result = await db.execute(select(ProjectORM))
        projects = result.scalars().all()
        return projects
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching projects"
        )


@router.post("/create")
async def create_project(
    project: ProjectSchema, db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new project.
    """
    try:
        project_orm = ProjectORM(**project.model_dump())
        db.add(project_orm)
        await db.commit()
        return project_orm
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating project: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail="Failed to create project")


@router.get("/get")
async def get_project(
    project_id: UUID = Path(..., description="The UUID of the project to get"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get a project by ID.
    """
    project = await db.get(ProjectORM, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")  
    return project


@router.put("/update")
async def update_project(
    project: ProjectUpdate, db: AsyncSession = Depends(get_db_session)
):
    """
    Update an existing project.
    """
    try:
        existing_project = await db.get(ProjectORM, project.id)
        if not existing_project:
            raise HTTPException(
                status_code=404, detail=f"Project with id {project.id} not found"
            )
        update_data = project.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field != "id" and value is not None:
                setattr(existing_project, field, value)
        await db.commit()
        return existing_project
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating project: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail="Failed to update project")


@router.delete("/delete", status_code=200)
async def delete_project(project_id: UUID, db: AsyncSession = Depends(get_db_session)):
    """
    Delete a project.
    """
    try:
        project = await db.get(ProjectORM, project_id)
        if not project:
            raise HTTPException(
                status_code=404, detail=f"Project with id {project_id} not found"
            )
        await db.delete(project)
        await db.commit()
        return {"message": f"Project with id {project_id} deleted successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting project: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="Internal server error while deleting project"
        )

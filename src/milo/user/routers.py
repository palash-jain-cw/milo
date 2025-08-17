from fastapi import APIRouter, Depends, HTTPException, Path
from milo.core.logger.logger_setup import loguru_setup
from milo.shared.dependencies import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from milo.user.models.orm import User as UserORM
from milo.user.models.schema import User as UserSchema
from milo.user.models.dto import UserUpdate
import traceback
from uuid import UUID
from typing import List

logger = loguru_setup()

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal Server Error"},
        400: {"description": "Bad Request"},
    },
)


@router.get("/list", response_model=List[UserSchema])
async def get_users(db: AsyncSession = Depends(get_db_session)):
    """
    List all users in the system.

    Returns a paginated list of users with their complete profile information.
    Each user object includes their ID, name, email, creation date, and status.
    """
    try:
        result = await db.execute(select(UserORM))
        users = result.scalars().all()
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching users"
        )


@router.post("/create", response_model=UserSchema, status_code=201)
async def create_user(user: UserSchema, db: AsyncSession = Depends(get_db_session)):
    """
    Create a new user.

    Create a new user account with the provided information. The email address must be unique.

    The request body should contain:
    - **name**: Full name of the user (2-50 characters)
    - **email**: Valid email address (must be unique)
    - **is_active**: Optional boolean to set initial account status (defaults to true)
    """
    try:
        user_orm = UserORM(**user.model_dump())
        db.add(user_orm)
        await db.commit()
        return user_orm
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=400,
            detail="Failed to create user. The email might already be in use.",
        )


@router.get("/get")
async def get_user(
    user_id: UUID = Path(..., description="The UUID of the user to get"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get a user by ID.
    """
    user = await db.get(UserORM, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return user


@router.put("/update")
async def update_user(
    user: UserUpdate, db: AsyncSession = Depends(get_db_session)
) -> UserSchema:
    """
    Update an existing user.

    Update one or more fields of an existing user. Only the provided fields will be updated.

    The request body should contain:
    - **id**: UUID of the user to update
    - **name**: Optional new name (2-50 characters)
    - **email**: Optional new email address (must be unique)
    - **is_active**: Optional boolean to update account status
    """
    try:
        # Get existing user
        existing_user = await db.get(UserORM, user.id)
        if not existing_user:
            raise HTTPException(
                status_code=404, detail=f"User with id {user.id} not found"
            )

        # Update only provided fields
        update_data = user.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field != "id" and value is not None:  # Skip id and None values
                setattr(existing_user, field, value)

        try:
            await db.commit()
            await db.refresh(existing_user)
            logger.info(f"Successfully updated user {existing_user.id}")
            return UserSchema.from_orm(existing_user)
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update user: {str(e)}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=400,
                detail="Failed to update user. The email might already be in use.",
            )

    except Exception as e:
        logger.error(f"Error in update_user: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="Internal server error while updating user"
        )


@router.delete("/delete", status_code=200)
async def delete_user(
    user_id: UUID = Path(..., description="The UUID of the user to delete"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Delete a user.

    Permanently delete a user from the system. This action cannot be undone.
    All associated data will be removed.
    """
    try:
        user = await db.get(UserORM, user_id)
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with id {user_id} not found"
            )
        await db.delete(user)
        await db.commit()
        return {"message": f"User with id {user_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting user: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="Internal server error while deleting user"
        )

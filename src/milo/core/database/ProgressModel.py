from pems_llm.core.database.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import Column, String, JSON, DateTime, Float, Integer
from sqlalchemy.future import select
from datetime import datetime
from pems_llm.core.config import get_settings
from pems_llm.core.logging_setup import loguru_setup
import traceback

settings = get_settings()
logger = loguru_setup()

# Create a separate engine and session factory for progress updates
progress_engine = create_async_engine(
    settings.database_url, echo=False, pool_size=5, max_overflow=10
)

progress_session_factory = async_sessionmaker(
    progress_engine, class_=AsyncSession, expire_on_commit=False
)


class ProgressModel(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String)
    task_name = Column(String)
    status = Column(String)
    payload = Column(JSON)
    progress = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


async def emit_progress(
    task_id: str,
    task_name: str,
    status: str,
    payload: dict = None,
    progress: float = None,
    db_session: AsyncSession = None,  # Keep for backward compatibility
):
    """
    Emit progress update using a dedicated session to avoid conflicts with main database operations.

    Args:
        task_id (str): Unique identifier for the task
        task_name (str): Name of the task
        status (str): Current status of the task
        payload (dict, optional): Additional data to store
        progress (float, optional): Progress percentage (0-100)
        db_session (AsyncSession, optional): Ignored as we use dedicated session
    """
    try:
        # Use a dedicated session for progress updates
        async with progress_session_factory() as progress_session:
            progress_session.add(
                ProgressModel(
                    task_id=task_id,
                    task_name=task_name,
                    status=status,
                    payload=payload,
                    progress=progress,
                )
            )
            await progress_session.commit()
            logger.debug(f"Progress update emitted for task {task_id}: {status}")
    except Exception as e:
        logger.error(
            f"Error emitting progress for task {task_id}: {str(e)}\n{traceback.format_exc()}"
        )
        # Don't raise the exception - progress updates should not break the main flow


async def get_progress(
    task_id: str, db_session: AsyncSession = None
):  # Keep for backward compatibility
    """
    Get the latest progress update for a task using the dedicated session.

    Args:
        task_id (str): The task ID to get progress for
        db_session (AsyncSession, optional): Ignored as we use dedicated session

    Returns:
        ProgressModel | None: The latest progress update or None if not found/error
    """
    try:
        async with progress_session_factory() as progress_session:
            result = await progress_session.execute(
                select(ProgressModel)
                .where(ProgressModel.task_id == task_id)
                .order_by(ProgressModel.created_at.desc())
            )
            return result.scalars().first()
    except Exception as e:
        logger.error(
            f"Error getting progress for task {task_id}: {str(e)}\n{traceback.format_exc()}"
        )
        return None

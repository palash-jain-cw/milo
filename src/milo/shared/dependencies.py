from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from milo.core.database.base import AsyncSessionLocal
from milo.core.logger.logger_setup import loguru_setup

logger = loguru_setup()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            # Test the connection
            await session.execute(text("SELECT 1"))
            yield session
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            await session.close()

import traceback
from sqlalchemy import text, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from milo.core.logger.logger_setup import loguru_setup
from milo.core.config import settings

logger = loguru_setup()

# Get database URL from environment variable
DATABASE_URL = settings.database_url

# Create async engine with PostgreSQL-specific settings
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True,
    # PostgreSQL specific settings
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,  # Adjust based on your needs
    max_overflow=10,  # Adjust based on your needs
    pool_timeout=30,  # Connection timeout in seconds
)

# Create async session factory with PostgreSQL-specific settings
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Prevent automatic flushing for better control
)


Base = declarative_base(metadata=MetaData(schema=settings.POSTGRES_SCHEMA))


# Dependency to get DB session
async def get_db():
    """Dependency provider for database sessions in FastAPI endpoints"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}\n{traceback.format_exc()}")
            raise
        finally:
            await session.close()


# Context manager for background tasks
async def get_async_session():
    """Async context manager for database sessions in background tasks"""
    async with AsyncSessionLocal() as session:
        try:
            return session
        except Exception as e:
            logger.error(
                f"Failed to create async session: {str(e)}\n{traceback.format_exc()}"
            )
            raise


async def get_async_session_local():
    async with AsyncSessionLocal() as session:
        try:
            # Test the connection
            await session.execute(text("SELECT 1"))
            print("Database connection successful!")
            return session
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            raise

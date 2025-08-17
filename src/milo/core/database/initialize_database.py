import asyncio
import sys
import traceback
from sqlalchemy import text
from milo.core.database.base import engine, Base
from milo.project.models.orm import Project
from milo.user.models.orm import User
from milo.core.logger.logger_setup import loguru_setup
from milo.core.config import settings

logger = loguru_setup()


async def drop_all_tables():
    """Drop only the tables that are defined in our SQLAlchemy models in the specified schema"""
    try:
        # Get list of tables managed by SQLAlchemy before dropping
        tables_to_drop = Base.metadata.tables.keys()
        logger.info(
            f"Tables that will be dropped from schema '{settings.POSTGRES_SCHEMA}': {tables_to_drop}"
        )

        # Drop only SQLAlchemy-managed tables in the specified schema
        async with engine.begin() as conn:
            # Set the search path to our schema
            await conn.execute(text(f"SET search_path TO {settings.POSTGRES_SCHEMA}"))
            await conn.run_sync(Base.metadata.drop_all)
            logger.info(
                f"Successfully dropped the following tables from schema '{settings.POSTGRES_SCHEMA}':"
            )
            for table in tables_to_drop:
                logger.info(f"  - {table}")

    except Exception as e:
        logger.error(f"Error dropping tables: {str(e)}\n{traceback.format_exc()}")
        raise


async def init_database():
    try:
        logger.info("Starting database initialization...")
        logger.info(f"Using database URL: {settings.database_url}")
        logger.info(f"Using schema: {settings.POSTGRES_SCHEMA}")

        async with engine.begin() as conn:
            # First verify the schema exists
            result = await conn.execute(
                text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = :schema
                )
                """),
                {"schema": settings.POSTGRES_SCHEMA},
            )
            if not result.scalar():
                raise Exception(f"Schema '{settings.POSTGRES_SCHEMA}' does not exist")

            # Set the search path to our schema
            await conn.execute(
                text(
                    f"ALTER DATABASE {settings.POSTGRES_DB} SET search_path TO {settings.POSTGRES_SCHEMA}, public"
                )
            )
            await conn.execute(
                text(f"SET search_path TO {settings.POSTGRES_SCHEMA}, public")
            )

            # Drop existing tables
            logger.info(
                f"Dropping existing tables in schema '{settings.POSTGRES_SCHEMA}'..."
            )
            await drop_all_tables()

            # Create all tables
            logger.info(
                f"Creating new tables in schema '{settings.POSTGRES_SCHEMA}'..."
            )
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Created all tables successfully")

            # Verify tables
            result = await conn.execute(
                text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema
                """),
                {"schema": settings.POSTGRES_SCHEMA},
            )
            tables = result.scalars().all()
            logger.info(
                f"Created tables in schema '{settings.POSTGRES_SCHEMA}': {tables}"
            )

        logger.success("Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}\n{traceback.format_exc()}")
        raise


def main():
    """
    Main function to run the database initialization
    """
    try:
        asyncio.run(init_database())
    except KeyboardInterrupt:
        logger.warning("Database initialization interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

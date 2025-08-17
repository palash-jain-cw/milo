import asyncio
import traceback
from sqlalchemy import text
from milo.core.database.base import engine, Base
from milo.core.logger.logger_setup import loguru_setup
from milo.core.config import settings

# Import all models to ensure they are registered with SQLAlchemy
from milo.user.models.orm import User  # noqa
from milo.project.models.orm import Project  # noqa

logger = loguru_setup()


async def verify_schema():
    """Verify that the schema exists"""
    async with engine.begin() as conn:
        try:
            # First, log all available schemas for debugging
            debug_result = await conn.execute(
                text("SELECT schema_name FROM information_schema.schemata")
            )
            all_schemas = [row[0] for row in debug_result]
            logger.debug(f"Available schemas in database: {all_schemas}")

            # Check for our specific schema
            result = await conn.execute(
                text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.schemata 
                    WHERE schema_name = :schema
                )
                """),
                {"schema": settings.POSTGRES_SCHEMA},
            )
            exists = result.scalar()

            if exists:
                logger.success(f"✅ Schema '{settings.POSTGRES_SCHEMA}' exists")
                return True
            else:
                # Try to create the schema if it doesn't exist
                try:
                    await conn.execute(
                        text(f"CREATE SCHEMA IF NOT EXISTS {settings.POSTGRES_SCHEMA}")
                    )
                    logger.info(f"Created schema '{settings.POSTGRES_SCHEMA}'")
                    return True
                except Exception as create_error:
                    logger.error(
                        f"❌ Schema '{settings.POSTGRES_SCHEMA}' does not exist and failed to create it: {str(create_error)}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error verifying schema: {str(e)}\n{traceback.format_exc()}")
            return False


async def verify_tables():
    """Verify that all expected tables exist with correct structure"""
    # Type mapping from PostgreSQL to SQLAlchemy types
    pg_to_sa_types = {
        "INTEGER": "Integer",
        "BIGINT": "BigInteger",
        "CHARACTER VARYING": "String",
        "TEXT": "Text",
        "TIMESTAMP WITHOUT TIME ZONE": "DateTime",
        "TIMESTAMP WITH TIME ZONE": "DateTime",
        "DOUBLE PRECISION": "Float",
        "BOOLEAN": "Boolean",
        "JSONB": "JSON",
        "JSON": "JSON",
        "UUID": "UUID",
        "DATE": "Date",
        # Add any custom enum types
        "USER-DEFINED": "Enum",  # For enum types like projectstatus
    }
    async with engine.begin() as conn:
        try:
            # Set search path to our schema
            await conn.execute(text(f"SET search_path TO {settings.POSTGRES_SCHEMA}"))

            # Get list of expected tables from SQLAlchemy models
            table_mapping = {
                table_name.split(".")[-1]: table_name
                for table_name in Base.metadata.tables.keys()
            }
            expected_tables = set(table_mapping.keys())

            # Get actual tables in the schema
            result = await conn.execute(
                text(
                    """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema
                """
                ),
                {"schema": settings.POSTGRES_SCHEMA},
            )
            actual_tables = set(row[0] for row in result)

            # Compare expected vs actual tables
            missing_tables = expected_tables - actual_tables
            extra_tables = actual_tables - expected_tables

            if missing_tables:
                logger.error(f"❌ Missing tables: {missing_tables}")
                return False

            if extra_tables:
                logger.warning(f"⚠️ Extra tables found: {extra_tables}")

            logger.success(f"✅ All expected tables exist: {expected_tables}")

            # Verify table structure for each table
            for table_name in expected_tables:
                # Get expected columns from SQLAlchemy model using the full table name
                full_table_name = table_mapping[table_name]
                expected_columns = {
                    column.name: column.type.__class__.__name__
                    for column in Base.metadata.tables[full_table_name].columns
                }

                # Get actual columns from database using information_schema
                result = await conn.execute(
                    text("""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale,
                        is_nullable
                    FROM information_schema.columns 
                    WHERE table_schema = :schema 
                    AND table_name = :table
                    """),
                    {"schema": settings.POSTGRES_SCHEMA, "table": table_name},
                )

                columns_info = result.fetchall()
                actual_columns = {}

                for col in columns_info:
                    pg_type = col.data_type.upper()
                    # Map PostgreSQL type to SQLAlchemy type
                    sa_type = pg_to_sa_types.get(pg_type)
                    if sa_type is None:
                        # If type not in mapping, use the original type
                        sa_type = pg_type.capitalize()
                        logger.warning(
                            f"Unknown type mapping for PostgreSQL type: {pg_type}"
                        )

                    actual_columns[col.column_name] = sa_type

                # Compare columns
                missing_columns = set(expected_columns.keys()) - set(
                    actual_columns.keys()
                )
                extra_columns = set(actual_columns.keys()) - set(
                    expected_columns.keys()
                )

                if missing_columns:
                    logger.error(
                        f"❌ Table '{table_name}' missing columns: {missing_columns}"
                    )
                    return False

                if extra_columns:
                    logger.warning(
                        f"⚠️ Table '{table_name}' has extra columns: {extra_columns}"
                    )

                # Compare column types
                for col_name, expected_type in expected_columns.items():
                    actual_type = actual_columns.get(col_name)
                    if actual_type != expected_type:
                        logger.error(
                            f"❌ Column type mismatch in '{table_name}.{col_name}': "
                            f"expected {expected_type}, got {actual_type}"
                        )
                        return False

                logger.success(f"✅ Table '{table_name}' structure is correct")

            return True

        except Exception as e:
            logger.error(f"Error verifying tables: {str(e)}\n{traceback.format_exc()}")
            return False


async def verify_database():
    """
    Verify that the database is initialized correctly.
    Returns True if everything is correct, False otherwise.
    """
    try:
        logger.info("Starting database verification...")
        logger.info(f"Using schema: {settings.POSTGRES_SCHEMA}")

        # Verify schema exists
        if not await verify_schema():
            return False

        # Verify tables
        if not await verify_tables():
            return False

        logger.success("✅ Database verification completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Error during verification: {str(e)}\n{traceback.format_exc()}")
        return False


def main():
    """Main function to run the database verification"""
    try:
        success = asyncio.run(verify_database())
        if not success:
            logger.error("❌ Database verification failed")
            exit(1)
    except KeyboardInterrupt:
        logger.warning("Database verification interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Failed to verify database: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()

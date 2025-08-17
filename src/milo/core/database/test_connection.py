import asyncio
from milo.core.database.base import get_async_session_local
import traceback


async def test_database_connection():
    try:
        session = await get_async_session_local()
        print("✅ Successfully connected to the database!")
        await session.close()
        return True
    except Exception as e:
        print("❌ Failed to connect to the database")
        print(f"Error: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    asyncio.run(test_database_connection())

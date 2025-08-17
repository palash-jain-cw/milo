"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from milo.core.logger.logger_setup import loguru_setup
from milo.user.routers import router as user_router
from milo.core.database.test_connection import test_database_connection
from milo.core.database.verify_database import verify_database

from milo.project.routers import router as project_router
from milo.task.routers import router as task_router

# Initialize logger
logger = loguru_setup()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.

    Args:
        app: The FastAPI application instance
    """
    # Startup
    logger.info("Starting up FastAPI application")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application")


# Create FastAPI application
app = FastAPI(
    title="Milo API",
    description="API for Milo application",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(user_router, prefix="/user", tags=["User Management"])
app.include_router(project_router, prefix="/project", tags=["Project Management"])
app.include_router(task_router, prefix="/task", tags=["Task Management"])


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root endpoint to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health Check"])
async def health():
    """Health check endpoint."""
    connection_status = await test_database_connection()
    database_status = await verify_database()
    if not connection_status:
        return {"status": "unhealthy", "reason": "Database connection failed"}
    if not database_status:
        return {"status": "unhealthy", "reason": "Database verification failed"}
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "milo.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=logging.INFO,
    )

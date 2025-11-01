"""Main application entry point - FastAPI server and CLI."""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from milo.core.logger.logger_setup import loguru_setup
from milo.core.config import settings

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


@app.get("/")
async def root():
    """Redirect root endpoint to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


def run_server():
    """Run the FastAPI server."""
    import uvicorn
    uvicorn.run(
        "milo.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=logging.INFO,
    )


def run_chat():
    """Run the interactive chat interface."""
    from milo.agents import interactive_chat
    from milo.shared.database import init_db
    from milo.tasks.models import create_sample_tasks
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Create sample tasks if needed
    try:
        create_sample_tasks()
        logger.info("Sample tasks created")
    except Exception as e:
        logger.warning(f"Could not create sample tasks: {e}")
    
    # Start interactive chat
    interactive_chat()


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        run_chat()
    else:
        run_server()

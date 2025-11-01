from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session
from milo.core.config import settings
from milo.tasks.models import Task

# -------------------------------------------------------------------
# DATABASE CONFIGURATION
# -------------------------------------------------------------------

DATABASE_URL = f"sqlite:///{settings.data_dir / 'milo.db'}"
engine = create_engine(DATABASE_URL, echo=False)


# -------------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------------


def init_db():
    """
    Create all tables defined in SQLModel metadata.
    Should be called once at app startup.
    """
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


# -------------------------------------------------------------------
# CONTEXT-MANAGED SESSION
# -------------------------------------------------------------------


@contextmanager
def get_session():
    """
    Context manager that yields a database session and closes it after use.

    Example:
        with get_session() as session:
            service = TaskService(session)
            service.create_task("Buy milk")
    """
    session = Session(engine, expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

"""Database session lifecycle and connection pool management."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import get_settings
from app.core.logging import logger
from app.db.models import Base

settings = get_settings()

# For SQLite, enable check_same_thread=False
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create database tables if they do not exist."""
    logger.info("Initializing database schema from %s", settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency yield for FastAPI request context."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

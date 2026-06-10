import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


def get_engine():
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite"):
        os.makedirs("data", exist_ok=True)
        return create_engine(db_url, connect_args={"check_same_thread": False})
    return create_engine(db_url)


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _add_column_if_missing(conn, table: str, column: str, col_type: str) -> None:
    """SQLite-safe column migration: add column only if it doesn't exist."""
    try:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
        logger.info("Migration: added column %s.%s", table, column)
    except Exception:
        pass  # column already exists


def init_db():
    """Create all tables and apply lightweight column migrations."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Migrate existing DBs that predate the translation fields
    with engine.begin() as conn:
        _add_column_if_missing(conn, "items", "title_zh", "VARCHAR(500)")
        _add_column_if_missing(conn, "items", "summary_zh", "TEXT")

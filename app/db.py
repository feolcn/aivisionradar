import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


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


def init_db():
    """Create all tables."""
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

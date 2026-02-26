import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Local dev defaults to SQLite; production sets DATABASE_URL to a PostgreSQL URI.
# Railway (and some other providers) emit "postgres://" — SQLAlchemy requires "postgresql://".
_raw_url = os.getenv("DATABASE_URL", "sqlite:///./data.db")
DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)

# check_same_thread is a SQLite-only option
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
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
    from app.models import CaseRecord  # noqa: F401 — ensure model is registered
    Base.metadata.create_all(bind=engine)

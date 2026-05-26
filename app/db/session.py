import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DEFAULT_DATABASE_URL = "sqlite:///./receipts.db"


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def is_sqlite_url(url: str) -> bool:
    return url.startswith("sqlite")


def get_database_url() -> str:
    return normalize_database_url(os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL)


def get_engine_kwargs(url: str) -> dict:
    kwargs = {"pool_pre_ping": True}
    if is_sqlite_url(url):
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


DATABASE_URL = get_database_url()

# DBエンジンの作成
engine = create_engine(
    DATABASE_URL,
    **get_engine_kwargs(DATABASE_URL),
)

# セッションの作成
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

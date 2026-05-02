# DB接続

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLiteを選択
DATABASE_URL = "sqlite:///./receipts.db"

# DBエンジンの作成
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
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
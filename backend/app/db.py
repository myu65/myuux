import os
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine


def build_engine(database_url: str):
    return create_engine(database_url, echo=False)


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workspace.db")
engine = build_engine(DATABASE_URL)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def init_db() -> None:
    SQLModel.metadata.create_all(engine)

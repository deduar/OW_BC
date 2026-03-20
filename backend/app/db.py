import os
from sqlmodel import create_engine, Session
from collections.abc import Generator

def get_url():
    user = os.getenv("DB_USER", "owbc")
    password = os.getenv("DB_PASSWORD", "owbc_pass")
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "5432")
    db = os.getenv("DB_NAME", "owbc")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(get_url())

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

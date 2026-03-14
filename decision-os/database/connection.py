from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
import os
import sqlite3
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DB_PATH = ROOT / "database" / "decision_os_local.db"
DEFAULT_SQLITE_URL = f"sqlite+pysqlite:///{LOCAL_DB_PATH}"

def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)


@lru_cache(maxsize=4)
def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)


def get_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(database_url),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


def get_session(database_url: str | None = None) -> Session:
    return get_session_factory(database_url)()


@contextmanager
def session_scope(database_url: str | None = None) -> Iterator[Session]:
    session = get_session(database_url)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_connection() -> sqlite3.Connection:
    # Local sqlite fallback retained for compatibility with earlier MVP code.
    database_url = get_database_url()
    if database_url.startswith("sqlite"):
        sqlite_path = database_url.replace("sqlite+pysqlite:///", "", 1)
    else:
        sqlite_path = os.getenv("DECISION_OS_SQLITE_PATH", str(LOCAL_DB_PATH))
    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    return connection

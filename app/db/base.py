from contextlib import contextmanager

from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False) if engine else None


def _ensure_mysql_database():
    """Creates the schema if it does not exist yet (MySQL only)."""
    url = make_url(DATABASE_URL)
    if url.get_backend_name() != "mysql" or not url.database:
        return
    # URL.set(database=None) would keep the current database, so build a server-level URL instead
    server_url = URL.create(url.drivername, url.username, url.password, url.host, url.port, query=url.query)
    server = create_engine(server_url)
    try:
        with server.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{url.database}` CHARACTER SET utf8mb4"))
            conn.commit()
    finally:
        server.dispose()


# create_all() never alters existing tables, so columns added after the first release are listed here
NEW_COLUMNS = [
    ("job_post", "genderRestriction", "VARCHAR(10) NOT NULL DEFAULT 'any'"),
    ("job_application", "aiAnalysis", "JSON NULL"),
]


def _add_missing_columns():
    inspector = inspect(engine)
    for table, column, ddl in NEW_COLUMNS:
        existing = {c["name"] for c in inspector.get_columns(table)}
        if column not in existing:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
            print(f"Migrated: added {table}.{column}")


def connect_to_database():
    if engine is None:
        print("DATABASE_URL is not set; database unavailable.")
        return
    try:
        _ensure_mysql_database()
        import app.db.models  # noqa: F401  (registers the tables)

        Base.metadata.create_all(engine)
        _add_missing_columns()
        print("Database connected successfully.")
    except Exception as e:
        print(f"Failed to connect to the database: {e}")


@contextmanager
def session_scope():
    """Yields a session, commits on success and rolls back on error."""
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except OperationalError:
        session.rollback()
        raise HTTPException(status_code=503, detail="Database unavailable")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def close_connection():
    if engine is not None:
        engine.dispose()

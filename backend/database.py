import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Railway sets DATABASE_URL env var for PostgreSQL; fallback to local SQLite
_env_url = os.getenv("DATABASE_URL")
if _env_url and _env_url.startswith("postgres"):
    # Railway PostgreSQL — use psycopg2
    DATABASE_URL = _env_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
else:
    _db_path = os.getenv("SQLITE_PATH") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "phantomgrid.db"
    )
    DATABASE_URL = f"sqlite:///{_db_path}"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from db.models import Base

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_DIR}/seo_engine.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    """Initializes tables and seeds base brands if empty."""
    Base.metadata.create_all(bind=engine)
    # Automatic migration helper for SQLite: add any missing columns in brands
    if "sqlite" in DATABASE_URL:
        with engine.connect() as conn:
            from sqlalchemy import text
            try:
                res = conn.execute(text("PRAGMA table_info(brands)"))
                existing_cols = {row[1] for row in res.fetchall()}
                if "brand_color_primary" not in existing_cols:
                    conn.execute(text("ALTER TABLE brands ADD COLUMN brand_color_primary VARCHAR(30) DEFAULT '#4f46e5'"))
                if "brand_color_accent" not in existing_cols:
                    conn.execute(text("ALTER TABLE brands ADD COLUMN brand_color_accent VARCHAR(30) DEFAULT '#7c3aed'"))
                conn.commit()
            except Exception:
                pass

def get_db():
    """Dependency helper for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

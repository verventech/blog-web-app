import sqlite3
from pathlib import Path
from sqlmodel import Session, create_engine

# Resolve path to root db/ directory: ../db/
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db"
DB_FILENAME = DB_DIR / "blog_app.db"
INIT_SQL_PATH = DB_DIR / "init.sql"


def init_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_FILENAME)
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(INIT_SQL_PATH, "r", encoding="utf-8") as file:
        conn.executescript(file.read())

    conn.commit()
    conn.close()


engine = create_engine(
    f"sqlite:///{DB_FILENAME}",
    connect_args={"check_same_thread": False},
)


def get_session():
    with Session(engine) as session:
        yield session
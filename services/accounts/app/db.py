"""Database connection and a tiny migration runner.

Migrations are plain .sql files in ../migrations, applied in name order.
Each applied file is recorded in schema_migrations, so it only runs once.
"""
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://app:app@localhost:5432/accounts")
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def get_conn():
    """FastAPI dependency: one connection per request, committed at the end."""
    with connect() as conn:
        yield conn


def run_migrations():
    with connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " version TEXT PRIMARY KEY,"
            " applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        applied = {row["version"] for row in conn.execute("SELECT version FROM schema_migrations")}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                continue
            conn.execute(path.read_text())
            conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,))
            print(f"Applied migration {path.name}")

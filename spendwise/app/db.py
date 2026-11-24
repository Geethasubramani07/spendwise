"""SQLite storage (standard library only)."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB = str(Path(__file__).resolve().parent.parent / "spendwise.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,
    description  TEXT NOT NULL,
    merchant     TEXT NOT NULL,
    amount       REAL NOT NULL,
    category     TEXT NOT NULL,
    anomaly      INTEGER NOT NULL DEFAULT 0,
    score        REAL NOT NULL DEFAULT 0,
    reason       TEXT NOT NULL DEFAULT '',
    fingerprint  TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_txn_ts ON transactions(ts);
CREATE TABLE IF NOT EXISTS budgets (
    category       TEXT PRIMARY KEY,
    monthly_limit  REAL NOT NULL
);
"""

DEFAULT_BUDGETS = {
    "Food": 6000,
    "Transport": 3000,
    "Shopping": 5000,
    "Bills": 4000,
    "Entertainment": 1500,
    "Health": 2000,
    "Education": 3000,
    "Other": 2000,
}


def get_conn(path: str | None = None) -> sqlite3.Connection:
    """Open a connection, create tables and seed default budgets."""
    db_path = path or os.environ.get("SPENDWISE_DB", DEFAULT_DB)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM budgets").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO budgets(category, monthly_limit) VALUES (?, ?)",
            list(DEFAULT_BUDGETS.items()),
        )
        conn.commit()
    return conn

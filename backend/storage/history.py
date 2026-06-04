"""
SQLite-backed session history store.

Persists assessment sessions and serialized risk reports for retrieval
via the /history and /report endpoints.
"""

from __future__ import annotations
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.config import settings


class HistoryStore:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or settings.db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    entity_name TEXT NOT NULL,
                    context_type TEXT,
                    industry TEXT,
                    status TEXT NOT NULL,
                    overall_score REAL,
                    overall_level TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    report_json TEXT,
                    error TEXT
                )
            """)
            conn.commit()

    def upsert_session(
        self,
        session_id: str,
        entity_name: str,
        context_type: str,
        industry: str,
        status: str,
        overall_score: float | None = None,
        overall_level: str | None = None,
        report: dict | None = None,
        error: str | None = None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        completed_at = now if status == "complete" else None
        report_json = json.dumps(report) if report else None

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions
                  (session_id, entity_name, context_type, industry, status,
                   overall_score, overall_level, created_at, completed_at, report_json, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                  status=excluded.status,
                  overall_score=excluded.overall_score,
                  overall_level=excluded.overall_level,
                  completed_at=excluded.completed_at,
                  report_json=excluded.report_json,
                  error=excluded.error
                """,
                (
                    session_id, entity_name, context_type, industry, status,
                    overall_score, overall_level, now, completed_at, report_json, error,
                ),
            )
            conn.commit()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()

        if not row:
            return None

        result = dict(row)
        if result.get("report_json"):
            result["report"] = json.loads(result.pop("report_json"))
        else:
            result.pop("report_json", None)

        return result

    def list_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT session_id, entity_name, context_type, industry,
                       status, overall_score, overall_level, created_at, completed_at
                FROM sessions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]


# Module-level singleton
store = HistoryStore()

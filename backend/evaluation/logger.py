"""
Evaluation and structured run logger.

Writes per-run JSON logs for monitoring, debugging, and future fine-tuning.
Each log entry records inputs, agent outputs, scores, timing, and errors.
"""

from __future__ import annotations
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.config import settings

# Standard Python logger — also used for console output
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("risk_assessor")


class RunLogger:
    """
    Writes structured JSON logs to LOG_DIR/YYYY-MM-DD.jsonl.
    Each line is a self-contained JSON record for a single assessment run.
    """

    def __init__(self, log_dir: str | None = None) -> None:
        self.log_dir = Path(log_dir or settings.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self) -> Path:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return self.log_dir / f"{date_str}.jsonl"

    def log_run(
        self,
        session_id: str,
        request_data: dict[str, Any],
        report_data: dict[str, Any] | None,
        node_trace: list[str],
        errors: list[str],
        duration_ms: int,
    ) -> None:
        record = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": duration_ms,
            "entity_name": request_data.get("name"),
            "industry": request_data.get("industry"),
            "context_type": request_data.get("context_type"),
            "overall_score": report_data.get("overall_score") if report_data else None,
            "overall_level": report_data.get("overall_level") if report_data else None,
            "finding_count": len(report_data.get("top_risks", [])) if report_data else 0,
            "node_trace": node_trace,
            "errors": errors,
            "success": not bool(errors) and report_data is not None,
        }

        with open(self._log_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        level = logging.WARNING if errors else logging.INFO
        logger.log(
            level,
            "Run %s | %s | score=%.0f | %dms | errors=%d",
            session_id,
            request_data.get("name", "?"),
            record["overall_score"] or 0,
            duration_ms,
            len(errors),
        )

    def log_error(self, session_id: str, error: str) -> None:
        logger.error("Run %s failed: %s", session_id, error)


# Module-level singleton
run_logger = RunLogger()

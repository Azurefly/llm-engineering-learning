from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .bank_quality import validate_question_bank
from .exam_v2 import _lang, _nav, db

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


def diagnostic_report() -> dict[str, Any]:
    with db.connect() as conn:
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0])
        busy_timeout = int(conn.execute("PRAGMA busy_timeout").fetchone()[0])
        tables = int(conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0])
    bank = validate_question_bank()
    data_dir = db.path.parent
    backup_dir = data_dir / "backups"
    runner_mode = os.getenv("LLM_CODE_RUNNER", "disabled").strip().lower()
    report = {
        "ok": integrity.lower() == "ok" and bank["ok"],
        "database": {
            "integrity": integrity,
            "journal_mode": journal_mode,
            "busy_timeout_ms": busy_timeout,
            "size_bytes": db.path.stat().st_size if db.path.exists() else 0,
            "table_count": tables,
            "path": str(db.path),
        },
        "question_bank": bank,
        "coding": {
            "runner": runner_mode,
            "enabled": runner_mode == "docker",
            "image": os.getenv("LLM_CODE_RUNNER_IMAGE", "llm-learning-sandbox:py312"),
        },
        "backup": {
            "snapshot_count": len(list(backup_dir.glob("pre-restore-*.json"))) if backup_dir.exists() else 0,
            "directory": str(backup_dir),
        },
    }
    return report


@router.get("/diagnostics", response_class=HTMLResponse)
def diagnostics_page(request: Request):
    lang = _lang(request)
    c = _nav(request, lang)
    c["report"] = diagnostic_report()
    return templates.TemplateResponse(request=request, name="diagnostics.html", context=c)


@router.get("/api/diagnostics")
def diagnostics_api():
    report = diagnostic_report()
    return JSONResponse(report, status_code=200 if report["ok"] else 503)

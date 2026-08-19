from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .backup import BackupError, restore_from_json
from .exam_v2 import _lang, _nav, db

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


def _restore_limit_bytes() -> int:
    try:
        mb = int(os.getenv("LLM_RESTORE_MAX_MB", "50"))
    except ValueError:
        mb = 50
    return max(1, min(mb, 500)) * 1024 * 1024


@router.get("/data-management", response_class=HTMLResponse)
def data_management(request: Request):
    lang = _lang(request)
    c = _nav(request, lang)
    backup_dir = db.backup_dir
    pre_restore = sorted(backup_dir.glob("pre-restore-*.json"), reverse=True)[:10] if backup_dir.exists() else []
    automatic = sorted(backup_dir.glob("auto-*.json"), reverse=True)[:10] if backup_dir.exists() else []
    c.update({
        "snapshots": [x.name for x in pre_restore],
        "automatic_backups": [x.name for x in automatic],
        "restore_limit_mb": _restore_limit_bytes() // (1024 * 1024),
        "status": request.query_params.get("status"),
    })
    return templates.TemplateResponse(request=request, name="data_management.html", context=c)


@router.post("/data-management/restore")
async def restore_backup(file: UploadFile = File(...), confirm: str = Form("")):
    if confirm != "replace":
        raise HTTPException(400, "Explicit restore confirmation is required")
    filename = file.filename or "backup.json"
    if not filename.lower().endswith(".json"):
        raise HTTPException(400, "Backup must be a JSON file")
    limit = _restore_limit_bytes()
    raw = await file.read(limit + 1)
    if len(raw) > limit:
        raise HTTPException(413, f"Backup file exceeds the configured {limit // (1024 * 1024)} MB limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "Backup must use UTF-8") from exc
    try:
        restored = restore_from_json(db, text, replace=True)
    except BackupError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(409, f"Restore failed: {exc}") from exc
    total = sum(restored.values())
    return RedirectResponse(f"/data-management?status=restored-{total}", status_code=303)

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .backup import BackupError, restore_from_json
from .exam_v2 import _lang, _nav, db

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


@router.get("/data-management", response_class=HTMLResponse)
def data_management(request: Request):
    lang = _lang(request)
    c = _nav(request, lang)
    backup_dir = db.path.parent / "backups"
    snapshots = sorted(backup_dir.glob("pre-restore-*.json"), reverse=True)[:10] if backup_dir.exists() else []
    c.update({"snapshots": [x.name for x in snapshots], "status": request.query_params.get("status")})
    return templates.TemplateResponse(request=request, name="data_management.html", context=c)


@router.post("/data-management/restore")
async def restore_backup(file: UploadFile = File(...)):
    filename = file.filename or "backup.json"
    if not filename.lower().endswith(".json"):
        raise HTTPException(400, "Backup must be a JSON file")
    raw = await file.read(10 * 1024 * 1024 + 1)
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(413, "Backup file is too large")
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

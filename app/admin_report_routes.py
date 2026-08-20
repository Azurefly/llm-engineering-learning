from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .admin import _admin
from .admin_reporting import collect_admin_report, user_progress_report
from .admin_settings import registration_enabled, set_registration_enabled
from .exam_v2 import _lang, _nav

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


@router.get("/admin/report", response_class=HTMLResponse)
def admin_report(request: Request):
    _admin(request)
    lang = _lang(request)
    c = _nav(request, lang)
    c.update(
        {
            "report": collect_admin_report(),
            "registration_enabled": registration_enabled(),
        }
    )
    return templates.TemplateResponse(request=request, name="admin_report.html", context=c)


@router.get("/admin/report/data")
def admin_report_data(request: Request):
    _admin(request)
    return JSONResponse(
        {
            "report": collect_admin_report(),
            "registration_enabled": registration_enabled(),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/users/{user_id}/progress", response_class=HTMLResponse)
def admin_user_progress(request: Request, user_id: int):
    _admin(request)
    report = user_progress_report(user_id)
    if not report:
        raise HTTPException(404, "User not found")
    lang = _lang(request)
    c = _nav(request, lang)
    c["progress_report"] = report
    return templates.TemplateResponse(request=request, name="admin_user_progress.html", context=c)


@router.post("/admin/settings/registration")
def admin_toggle_registration(request: Request, action: str = Form(...), next: str = Form("/admin/users")):
    actor = _admin(request)
    if action not in {"enable", "disable"}:
        raise HTTPException(400, "Invalid registration action")
    set_registration_enabled(action == "enable", actor_id=int(actor["id"]))
    target = next if next.startswith("/") and not next.startswith("//") else "/admin/users"
    separator = "&" if "?" in target else "?"
    status = "registration-enabled" if action == "enable" else "registration-disabled"
    return RedirectResponse(target + separator + "status=" + quote(status), status_code=303)

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import (
    SESSION_COOKIE,
    VALID_ROLES,
    _validate_password,
    _validate_username,
    account_store,
)
from .exam_v2 import _lang, _nav

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


def _user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(401, "Authentication required")
    return user


def _admin(request: Request) -> dict:
    user = _user(request)
    if str(user.get("role") or "user") != "superadmin":
        raise HTTPException(403, "Superadmin permission required")
    return user


def _admin_redirect(*, status: str | None = None, error: str | None = None) -> RedirectResponse:
    if error:
        return RedirectResponse("/admin/users?error=" + quote(error), status_code=303)
    return RedirectResponse("/admin/users" + ("?status=" + quote(status) if status else ""), status_code=303)


def _account_redirect(*, status: str | None = None, error: str | None = None) -> RedirectResponse:
    if error:
        return RedirectResponse("/account?error=" + quote(error), status_code=303)
    return RedirectResponse("/account" + ("?status=" + quote(status) if status else ""), status_code=303)


@router.get("/account", response_class=HTMLResponse)
def account_page(request: Request):
    current = _user(request)
    lang = _lang(request)
    fresh = account_store().get_user_by_id(int(current["id"])) or current
    c = _nav(request, lang)
    c.update(
        {
            "account": fresh,
            "status": request.query_params.get("status"),
            "error": request.query_params.get("error"),
        }
    )
    return templates.TemplateResponse(request=request, name="account.html", context=c)


@router.post("/account/profile")
def account_profile(request: Request, username: str = Form(...), display_name: str = Form("")):
    current = _user(request)
    error = _validate_username(username)
    if error:
        return _account_redirect(error=error)
    try:
        account_store().update_identity(int(current["id"]), username, display_name)
    except ValueError as exc:
        return _account_redirect(error=str(exc))
    return _account_redirect(status="profile-saved")


@router.post("/account/password")
def account_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    new_password_confirm: str = Form(...),
):
    current = _user(request)
    error = _validate_password(new_password)
    if error:
        return _account_redirect(error=error)
    if new_password != new_password_confirm:
        return _account_redirect(error="两次输入的新密码不一致。")
    try:
        account_store().change_password(int(current["id"]), current_password, new_password)
    except ValueError as exc:
        return _account_redirect(error=str(exc))
    # Password changes invalidate every session for this account, including the
    # current browser, so the new credential is required immediately.
    response = RedirectResponse("/login?changed=1", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.get("/admin/users", response_class=HTMLResponse)
def admin_users(request: Request):
    current = _admin(request)
    lang = _lang(request)
    c = _nav(request, lang)
    c.update(
        {
            "users": account_store().list_users(),
            "admin_user": current,
            "roles": sorted(VALID_ROLES),
            "registration_enabled": __import__("app.auth", fromlist=["registration_enabled"]).registration_enabled(),
            "status": request.query_params.get("status"),
            "error": request.query_params.get("error"),
        }
    )
    return templates.TemplateResponse(request=request, name="admin_users.html", context=c)


@router.post("/admin/users/create")
def admin_create_user(
    request: Request,
    username: str = Form(...),
    display_name: str = Form(""),
    password: str = Form(...),
    password_confirm: str = Form(...),
    role: str = Form("user"),
):
    actor = _admin(request)
    error = _validate_username(username) or _validate_password(password)
    if error:
        return _admin_redirect(error=error)
    if password != password_confirm:
        return _admin_redirect(error="两次输入的密码不一致。")
    if role not in VALID_ROLES:
        return _admin_redirect(error="无效的用户角色。")
    store = account_store()
    try:
        created, _ = store.create_user(username, display_name, password)
        if role != created.get("role"):
            store.set_role(int(actor["id"]), int(created["id"]), role)
    except ValueError as exc:
        return _admin_redirect(error=str(exc))
    return _admin_redirect(status="created")


@router.post("/admin/users/{user_id}/profile")
def admin_update_profile(
    request: Request,
    user_id: int,
    username: str = Form(...),
    display_name: str = Form(""),
):
    _admin(request)
    error = _validate_username(username)
    if error:
        return _admin_redirect(error=error)
    try:
        account_store().update_identity(user_id, username, display_name)
    except ValueError as exc:
        return _admin_redirect(error=str(exc))
    return _admin_redirect(status="updated")


@router.post("/admin/users/{user_id}/status")
def admin_set_status(request: Request, user_id: int, action: str = Form(...)):
    actor = _admin(request)
    if action not in {"enable", "disable"}:
        return _admin_redirect(error="无效的账号状态操作。")
    try:
        account_store().set_active(int(actor["id"]), user_id, action == "enable")
    except ValueError as exc:
        return _admin_redirect(error=str(exc))
    return _admin_redirect(status="status-updated")


@router.post("/admin/users/{user_id}/role")
def admin_set_role(request: Request, user_id: int, role: str = Form(...)):
    actor = _admin(request)
    try:
        account_store().set_role(int(actor["id"]), user_id, role)
    except ValueError as exc:
        return _admin_redirect(error=str(exc))
    return _admin_redirect(status="role-updated")


@router.post("/admin/users/{user_id}/password")
def admin_reset_password(
    request: Request,
    user_id: int,
    new_password: str = Form(...),
    new_password_confirm: str = Form(...),
):
    actor = _admin(request)
    if int(actor["id"]) == int(user_id):
        return _admin_redirect(error="请在“我的账号”中修改自己的密码。")
    error = _validate_password(new_password)
    if error:
        return _admin_redirect(error=error)
    if new_password != new_password_confirm:
        return _admin_redirect(error="两次输入的新密码不一致。")
    try:
        account_store().reset_password(user_id, new_password)
    except ValueError as exc:
        return _admin_redirect(error=str(exc))
    return _admin_redirect(status="password-reset")

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import sqlite3
import unicodedata
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib.parse import quote

from fastapi import APIRouter, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .user_context import UserContext, reset_current_user, set_current_user

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
SESSION_COOKIE = "llm_session"
PBKDF2_ITERATIONS = 310_000
PUBLIC_PATHS = {"/login", "/register", "/health", "/favicon.ico"}
router = APIRouter()
templates = Jinja2Templates(directory=APP_DIR / "templates")


def data_dir() -> Path:
    path = Path(os.getenv("LLM_LEARNING_DATA_DIR", str(REPO_ROOT / "data")))
    path.mkdir(parents=True, exist_ok=True)
    return path


def registration_enabled() -> bool:
    return os.getenv("LLM_ALLOW_REGISTRATION", "1").strip().lower() not in {"0", "false", "no", "off"}


def _session_days() -> int:
    try:
        value = int(os.getenv("LLM_SESSION_DAYS", "30"))
    except ValueError:
        value = 30
    return max(1, min(value, 90))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat(timespec="seconds")


def _username_key(username: str) -> str:
    return unicodedata.normalize("NFKC", username.strip()).casefold()


def _validate_username(username: str) -> str | None:
    value = username.strip()
    if len(value) < 3 or len(value) > 32:
        return "用户名长度需要为 3～32 个字符。"
    if not all(ch.isalnum() or ch in "._-" for ch in value):
        return "用户名只能包含字母、数字、点、下划线和连字符。"
    return None


def _validate_password(password: str) -> str | None:
    if len(password) < 8:
        return "密码至少需要 8 个字符。"
    if len(password) > 128:
        return "密码不能超过 128 个字符。"
    return None


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=32)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        if iterations < 100_000 or iterations > 2_000_000:
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, base64.binascii.Error):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AccountStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init(self) -> None:
        with self.connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    username_key TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    storage_key TEXT NOT NULL UNIQUE,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_login_at TEXT
                );
                CREATE TABLE IF NOT EXISTS auth_sessions(
                    token_hash TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id, expires_at);
                """
            )

    def user_count(self) -> int:
        with self.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])

    def create_user(self, username: str, display_name: str, password: str) -> tuple[dict[str, Any], bool]:
        username = unicodedata.normalize("NFKC", username.strip())
        key = _username_key(username)
        display_name = unicodedata.normalize("NFKC", display_name.strip())[:64] or username
        ts = _now_iso()
        storage_key = uuid.uuid4().hex
        with self.connect() as conn:
            # Serialize the first-user decision so two concurrent registrations cannot
            # both claim the legacy single-user learning database.
            conn.execute("BEGIN IMMEDIATE")
            first = int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]) == 0
            try:
                cur = conn.execute(
                    """INSERT INTO users(username,username_key,display_name,password_hash,storage_key,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (username, key, display_name, hash_password(password), storage_key, ts, ts),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("用户名已经存在。") from exc
            user_id = int(cur.lastrowid)
            row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row), first

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE username_key=? AND is_active=1", (_username_key(username),)).fetchone()
        return dict(row) if row else None

    def verify_login(self, username: str, password: str) -> dict[str, Any] | None:
        user = self.get_user_by_username(username)
        if not user or not verify_password(password, str(user["password_hash"])):
            return None
        ts = _now_iso()
        with self.connect() as conn:
            conn.execute("UPDATE users SET last_login_at=?,updated_at=? WHERE id=?", (ts, ts, user["id"]))
        return user

    def create_session(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        created = _now()
        expires = created + timedelta(days=_session_days())
        with self.connect() as conn:
            conn.execute("DELETE FROM auth_sessions WHERE expires_at < ?", (_now_iso(),))
            conn.execute(
                "INSERT INTO auth_sessions(token_hash,user_id,created_at,expires_at,last_seen_at) VALUES(?,?,?,?,?)",
                (_token_hash(token), int(user_id), created.isoformat(timespec="seconds"), expires.isoformat(timespec="seconds"), created.isoformat(timespec="seconds")),
            )
        return token

    def user_for_session(self, token: str) -> dict[str, Any] | None:
        if not token or len(token) > 256:
            return None
        digest = _token_hash(token)
        with self.connect() as conn:
            row = conn.execute(
                """SELECT u.* FROM auth_sessions s JOIN users u ON u.id=s.user_id
                   WHERE s.token_hash=? AND s.expires_at>? AND u.is_active=1""",
                (digest, _now_iso()),
            ).fetchone()
        return dict(row) if row else None

    def delete_session(self, token: str) -> None:
        if not token:
            return
        with self.connect() as conn:
            conn.execute("DELETE FROM auth_sessions WHERE token_hash=?", (_token_hash(token),))


_STORES: dict[str, AccountStore] = {}


def account_store() -> AccountStore:
    path = data_dir() / "accounts.db"
    key = str(path.resolve())
    store = _STORES.get(key)
    if store is None:
        store = AccountStore(path)
        _STORES[key] = store
    return store


def user_learning_path(storage_key: str) -> Path:
    return data_dir() / "users" / storage_key / "learning.db"


def _legacy_has_learning_data(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        with sqlite3.connect(path) as conn:
            tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            for table in ("lesson_progress", "thoughts", "resources", "exam_attempts", "code_attempts", "adaptive_sessions"):
                if table in tables and int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) > 0:
                    return True
    except sqlite3.DatabaseError:
        return False
    return False


def claim_legacy_learning_data(storage_key: str) -> bool:
    source = data_dir() / "learning.db"
    target = user_learning_path(storage_key)
    if target.exists() or not _legacy_has_learning_data(source):
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
        src.backup(dst)
    return True


def _safe_next(value: str | None) -> str:
    value = (value or "/").strip()
    if not value.startswith("/") or value.startswith("//") or "\n" in value or "\r" in value:
        return "/"
    return value


def _set_session_cookie(response: RedirectResponse, request: Request, token: str) -> None:
    secure = request.url.scheme == "https" or os.getenv("LLM_COOKIE_SECURE", "0").strip().lower() in {"1", "true", "yes", "on"}
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=_session_days() * 24 * 3600,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def _render_auth(request: Request, template: str, *, error: str | None = None, username: str = "", display_name: str = "", status_code: int = 200):
    lang = "en" if (request.cookies.get("lang") or "").lower() == "en" else "zh-CN"
    return templates.TemplateResponse(
        request=request,
        name=template,
        status_code=status_code,
        context={
            "request": request,
            "lang": lang,
            "error": error,
            "username": username,
            "display_name": display_name,
            "registration_enabled": registration_enabled(),
        },
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if getattr(request.state, "user", None):
        return RedirectResponse("/", status_code=303)
    return _render_auth(request, "login.html")


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), next: str = Form("/")):
    if getattr(request.state, "user", None):
        return RedirectResponse("/", status_code=303)
    if len(username) > 64 or len(password) > 128:
        return _render_auth(request, "login.html", error="用户名或密码不正确。", username=username[:64], status_code=400)
    user = account_store().verify_login(username, password)
    if not user:
        return _render_auth(request, "login.html", error="用户名或密码不正确。", username=username, status_code=401)
    token = account_store().create_session(int(user["id"]))
    response = RedirectResponse(_safe_next(next), status_code=303)
    _set_session_cookie(response, request, token)
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    if getattr(request.state, "user", None):
        return RedirectResponse("/", status_code=303)
    return _render_auth(request, "register.html", status_code=200 if registration_enabled() else 403)


@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    display_name: str = Form(""),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    if not registration_enabled():
        raise HTTPException(403, "Registration is disabled")
    if getattr(request.state, "user", None):
        return RedirectResponse("/", status_code=303)
    error = _validate_username(username) or _validate_password(password)
    if password != password_confirm:
        error = error or "两次输入的密码不一致。"
    if error:
        return _render_auth(request, "register.html", error=error, username=username, display_name=display_name, status_code=400)
    try:
        user, is_first = account_store().create_user(username, display_name, password)
    except ValueError as exc:
        return _render_auth(request, "register.html", error=str(exc), username=username, display_name=display_name, status_code=409)
    if is_first:
        claim_legacy_learning_data(str(user["storage_key"]))
    token = account_store().create_session(int(user["id"]))
    response = RedirectResponse("/", status_code=303)
    _set_session_cookie(response, request, token)
    return response


@router.post("/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE, "")
    account_store().delete_session(token)
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


def _is_public(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith("/static/") or path.startswith("/language/")


def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return request.method == "GET" and ("text/html" in accept or "*/*" in accept or not accept)


def install_auth(app: FastAPI, *, initializer: Callable[[], None] | None = None) -> None:
    if getattr(app.state, "auth_installed", False):
        return
    initialized_users: set[str] = set()

    @app.middleware("http")
    async def authentication(request: Request, call_next):
        if os.getenv("LLM_AUTH_TEST_BYPASS", "0").strip().lower() in {"1", "true", "yes", "on"}:
            request.state.user = {"id": 0, "username": "test", "display_name": "Test User", "storage_key": "test"}
            return await call_next(request)

        store = account_store()
        user = store.user_for_session(request.cookies.get(SESSION_COOKIE, ""))
        request.state.user = user
        if user is None:
            if _is_public(request.url.path):
                response = await call_next(request)
                response.headers.setdefault("Cache-Control", "no-store")
                return response
            if _wants_html(request):
                target = quote(_safe_next(request.url.path + ("?" + request.url.query if request.url.query else "")), safe="/?=&%")
                return RedirectResponse(f"/login?next={target}", status_code=303)
            return JSONResponse({"detail": "Authentication required"}, status_code=401, headers={"Cache-Control": "no-store"})

        ctx = UserContext(
            user_id=int(user["id"]),
            storage_key=str(user["storage_key"]),
            username=str(user["username"]),
            display_name=str(user["display_name"]),
        )
        token = set_current_user(ctx)
        try:
            if initializer and ctx.storage_key not in initialized_users:
                initializer()
                initialized_users.add(ctx.storage_key)
            response = await call_next(request)
            return response
        finally:
            reset_current_user(token)

    app.state.auth_installed = True

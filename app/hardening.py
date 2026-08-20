from __future__ import annotations

import os
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware


def _allowed_hosts() -> list[str]:
    configured = [x.strip() for x in os.getenv("LLM_ALLOWED_HOSTS", "").split(",") if x.strip()]
    return configured or ["127.0.0.1", "localhost", "[::1]", "testserver"]


def _same_origin(request: Request) -> bool:
    if request.headers.get("sec-fetch-site", "").lower() == "cross-site":
        return False
    request_host = request.headers.get("host", "").lower()
    origin = request.headers.get("origin")
    if origin:
        try:
            return urlsplit(origin).netloc.lower() == request_host
        except ValueError:
            return False
    referer = request.headers.get("referer")
    if referer:
        try:
            return urlsplit(referer).netloc.lower() == request_host
        except ValueError:
            return False
    # CLI clients and local scripts commonly send neither Origin nor Referer.
    return True


def install_security_headers(app: FastAPI) -> None:
    if getattr(app.state, "security_headers_installed", False):
        return

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts())

    @app.middleware("http")
    async def local_request_hardening(request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not _same_origin(request):
            return PlainTextResponse("Cross-site write request blocked", status_code=403)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        sensitive = (
            request.url.path in {"/backup.json", "/api/diagnostics", "/account"}
            or request.url.path.startswith("/admin/")
        )
        if sensitive:
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    app.state.security_headers_installed = True

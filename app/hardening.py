from __future__ import annotations

from fastapi import FastAPI, Request


def install_security_headers(app: FastAPI) -> None:
    if getattr(app.state, "security_headers_installed", False):
        return

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if request.url.path in {"/backup.json", "/api/diagnostics"}:
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    app.state.security_headers_installed = True

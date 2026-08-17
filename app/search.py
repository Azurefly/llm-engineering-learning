from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .course import LESSONS, load_lesson_markdown, title_for
from .exam_v2 import _lang, _nav, db

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")
REPO_ROOT = Path(__file__).resolve().parent.parent


def _snippet(text: str, query: str, width: int = 180) -> str:
    cleaned = " ".join((text or "").replace("#", " ").replace("`", " ").split())
    pos = cleaned.lower().find(query.lower())
    if pos < 0:
        return cleaned[:width]
    start = max(0, pos - width // 3)
    end = min(len(cleaned), start + width)
    prefix = "…" if start else ""
    suffix = "…" if end < len(cleaned) else ""
    return prefix + cleaned[start:end] + suffix


def search_workspace(query: str, lang: str, limit: int = 50) -> list[dict[str, Any]]:
    q = " ".join((query or "").strip().split())[:120]
    if len(q) < 2:
        return []
    needle = q.lower()
    results: list[dict[str, Any]] = []

    for lesson in LESSONS:
        text, _ = load_lesson_markdown(REPO_ROOT, lesson, lang)
        title = title_for(lesson, lang)
        if needle in title.lower() or needle in text.lower():
            results.append({"kind": "course", "title": f"Week {lesson.week} · {title}", "snippet": _snippet(text, q), "url": f"/course/{lesson.key}"})

    with db.connect() as conn:
        pattern = f"%{q}%"
        thoughts = conn.execute(
            """SELECT id,title,content,tags,lesson_key FROM thoughts
               WHERE title LIKE ? COLLATE NOCASE OR content LIKE ? COLLATE NOCASE OR tags LIKE ? COLLATE NOCASE
               ORDER BY updated_at DESC LIMIT 30""",
            (pattern, pattern, pattern),
        ).fetchall()
        resources = conn.execute(
            """SELECT id,title,url,description,tags,lesson_key FROM resources
               WHERE title LIKE ? COLLATE NOCASE OR description LIKE ? COLLATE NOCASE OR tags LIKE ? COLLATE NOCASE OR url LIKE ? COLLATE NOCASE
               ORDER BY updated_at DESC LIMIT 30""",
            (pattern, pattern, pattern, pattern),
        ).fetchall()

    for row in thoughts:
        item = dict(row)
        results.append({"kind": "thought", "title": item["title"], "snippet": _snippet(f"{item['tags']} {item['content']}", q), "url": f"/thoughts/{item['id']}/edit"})
    for row in resources:
        item = dict(row)
        results.append({"kind": "resource", "title": item["title"], "snippet": _snippet(f"{item['tags']} {item['description']} {item['url']}", q), "url": f"/resources/{item['id']}/edit"})
    return results[:limit]


@router.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: str = ""):
    lang = _lang(request)
    query = " ".join((q or "").strip().split())[:120]
    c = _nav(request, lang)
    c.update({"query": query, "results": search_workspace(query, lang) if query else []})
    return templates.TemplateResponse(request=request, name="search.html", context=c)

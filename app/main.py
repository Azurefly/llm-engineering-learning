from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

import bleach
import mistune
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .backup import export_all_json
from .course import LESSONS, LESSON_MAP, load_lesson_markdown, title_for
from .db import Database
from .exam_system import exam_summary, router as exam_router
from .i18n import normalize_lang, tr

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
DATA_DIR = Path(os.getenv("LLM_LEARNING_DATA_DIR", str(REPO_ROOT / "data")))
DB_PATH = DATA_DIR / "learning.db"

app = FastAPI(title="LLM Engineering Learning", docs_url="/api/docs", redoc_url=None)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")
db = Database(DB_PATH)
markdown = mistune.create_markdown(plugins=["table", "task_lists", "strikethrough", "url"])
app.include_router(exam_router)

ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS).union({"p","pre","code","hr","br","h1","h2","h3","h4","h5","h6","table","thead","tbody","tr","th","td","ul","ol","li","blockquote","input","del","span","div"})
ALLOWED_ATTRS = {"a": ["href","title","target","rel"], "input": ["type","checked","disabled"], "code": ["class"], "span": ["class"]}


def render_markdown(text: str) -> str:
    raw = markdown(text or "")
    clean = bleach.clean(raw, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, protocols=["http","https","mailto"], strip=True)
    return bleach.linkify(clean, callbacks=[])


def get_lang(request: Request) -> str:
    return normalize_lang(request.query_params.get("lang") or request.cookies.get("lang"))


def nav_context(request: Request, lang: str) -> dict:
    progress = db.all_progress()
    lessons = [{"key": l.key, "week": l.week, "title": title_for(l, lang), "progress": progress.get(l.key, {"status":"not_started","percent":0,"score":None})} for l in LESSONS]
    return {"request": request, "lang": lang, "t": lambda key: tr(lang,key), "lessons": lessons, "current_path": request.url.path}


def average_progress(progress: dict) -> float:
    values = [int(progress.get(l.key, {}).get("percent",0)) for l in LESSONS]
    return round(sum(values)/len(values),1) if values else 0.0


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    lang = get_lang(request); progress = db.all_progress(); context = nav_context(request, lang)
    context.update({"overall": average_progress(progress), "stats": db.stats(), "thoughts": db.list_thoughts()[:5], "resources": db.list_resources()[:5]})
    response = templates.TemplateResponse(request=request, name="dashboard.html", context=context)
    response.set_cookie("lang", lang, max_age=31536000, samesite="lax")
    return response


@app.get("/language/{lang}")
def set_language(lang: str, next: str = "/"):
    lang = normalize_lang(lang)
    if not next.startswith("/") or next.startswith("//"): next = "/"
    response = RedirectResponse(next, status_code=303); response.set_cookie("lang", lang, max_age=31536000, samesite="lax"); return response


@app.get("/course/{lesson_key}", response_class=HTMLResponse)
def course(request: Request, lesson_key: str):
    lesson = LESSON_MAP.get(lesson_key)
    if not lesson: raise HTTPException(404)
    lang = get_lang(request); text, source = load_lesson_markdown(REPO_ROOT, lesson, lang)
    progress = db.all_progress().get(lesson_key, {"status":"not_started","percent":0,"score":None})
    context = nav_context(request,lang); context.update({"lesson":lesson,"lesson_title":title_for(lesson,lang),"content_html":render_markdown(text),"source":source,"lesson_progress":progress,"lesson_thoughts":db.list_thoughts(lesson_key)[:6],"lesson_resources":db.list_resources(lesson_key)[:6],"exam_summary":exam_summary(lesson_key)})
    return templates.TemplateResponse(request=request, name="course.html", context=context)


@app.post("/course/{lesson_key}/progress")
def update_progress(lesson_key: str, percent: int=Form(0)):
    if lesson_key not in LESSON_MAP: raise HTTPException(404)
    current = db.all_progress().get(lesson_key, {"status":"not_started","percent":0,"score":None})
    if current.get("status") == "completed":
        return RedirectResponse(f"/course/{lesson_key}", status_code=303)
    percent = max(0, min(99, int(percent)))
    status = "in_progress" if percent > 0 else "not_started"
    db.set_progress(lesson_key, status, percent, current.get("score"))
    return RedirectResponse(f"/course/{lesson_key}",status_code=303)


@app.get("/thoughts", response_class=HTMLResponse)
def thoughts(request: Request, lesson: str|None=None):
    lang=get_lang(request); c=nav_context(request,lang); c.update({"items":db.list_thoughts(lesson),"filter_lesson":lesson}); return templates.TemplateResponse(request=request,name="thoughts.html",context=c)


@app.get("/thoughts/new", response_class=HTMLResponse)
def new_thought(request: Request, lesson: str|None=None):
    lang=get_lang(request); c=nav_context(request,lang); c["item"]={"id":None,"title":"","content":"","tags":"","lesson_key":lesson or "","language":lang}; return templates.TemplateResponse(request=request,name="thought_edit.html",context=c)


@app.get("/thoughts/{item_id}/edit", response_class=HTMLResponse)
def edit_thought(request: Request, item_id: int):
    item=db.get_thought(item_id)
    if not item: raise HTTPException(404)
    lang=get_lang(request); c=nav_context(request,lang); c["item"]=item; return templates.TemplateResponse(request=request,name="thought_edit.html",context=c)


@app.post("/thoughts/save")
def save_thought(request: Request, item_id: str=Form(""), title: str=Form(...), content: str=Form(""), tags: str=Form(""), lesson_key: str=Form("")):
    lang=get_lang(request); db.save_thought(int(item_id) if item_id else None,title=title.strip(),content=content,tags=tags.strip(),lesson_key=lesson_key,language=lang); return RedirectResponse(f"/course/{lesson_key}" if lesson_key else "/thoughts",status_code=303)


@app.post("/thoughts/{item_id}/delete")
def delete_thought(item_id:int): db.delete_thought(item_id); return RedirectResponse("/thoughts",status_code=303)


@app.get("/resources", response_class=HTMLResponse)
def resources(request: Request, lesson: str|None=None):
    lang=get_lang(request); c=nav_context(request,lang); c.update({"items":db.list_resources(lesson),"filter_lesson":lesson}); return templates.TemplateResponse(request=request,name="resources.html",context=c)


@app.get("/resources/new", response_class=HTMLResponse)
def new_resource(request: Request, lesson: str|None=None):
    lang=get_lang(request); c=nav_context(request,lang); c["item"]={"id":None,"title":"","url":"","description":"","tags":"","lesson_key":lesson or "","language":lang}; return templates.TemplateResponse(request=request,name="resource_edit.html",context=c)


@app.get("/resources/{item_id}/edit", response_class=HTMLResponse)
def edit_resource(request: Request,item_id:int):
    item=db.get_resource(item_id)
    if not item: raise HTTPException(404)
    lang=get_lang(request); c=nav_context(request,lang); c["item"]=item; return templates.TemplateResponse(request=request,name="resource_edit.html",context=c)


@app.post("/resources/save")
def save_resource(request:Request,item_id:str=Form(""),title:str=Form(...),url:str=Form(...),description:str=Form(""),tags:str=Form(""),lesson_key:str=Form("")):
    lang=get_lang(request); parsed=urlparse(url.strip())
    if parsed.scheme not in {"http","https"} or not parsed.netloc: raise HTTPException(400,"URL must start with http:// or https://")
    db.save_resource(int(item_id) if item_id else None,title=title.strip(),url=url.strip(),description=description,tags=tags.strip(),lesson_key=lesson_key,language=lang); return RedirectResponse(f"/course/{lesson_key}" if lesson_key else "/resources",status_code=303)


@app.post("/resources/{item_id}/delete")
def delete_resource(item_id:int): db.delete_resource(item_id); return RedirectResponse("/resources",status_code=303)


@app.get("/backup.json")
def export_backup(): return Response(export_all_json(db),media_type="application/json; charset=utf-8",headers={"Content-Disposition":"attachment; filename=llm-learning-backup.json"})


@app.get("/health")
def health(): return {"status":"ok","db":str(DB_PATH)}

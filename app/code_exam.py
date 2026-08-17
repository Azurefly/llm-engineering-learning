from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .code_runner import CodeRunRequest, get_code_runner
from .course import LESSONS, LESSON_MAP, title_for
from .db import Database, now_iso
from .exam_v2 import DB_PATH
from .i18n import normalize_lang, tr

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")
db = Database(DB_PATH)


@dataclass(frozen=True)
class CodeChallenge:
    key: str
    lesson_key: str
    zh: str
    en: str
    prompt_zh: str
    prompt_en: str
    starter: str
    tests: str
    pass_score: int = 80


CHALLENGES: dict[str, CodeChallenge] = {
    "week02": CodeChallenge(
        "stable-softmax",
        "week02",
        "稳定 Softmax",
        "Stable Softmax",
        "实现 stable_softmax(logits)。返回与输入等长的概率列表；概率和为 1；需要能处理 [1000, 1001, 1002] 这类大数而不溢出。",
        "Implement stable_softmax(logits). Return a probability list of equal length, summing to 1, and handle large logits such as [1000, 1001, 1002] without overflow.",
        """import math\n\ndef stable_softmax(logits):\n    # TODO\n    raise NotImplementedError\n""",
        """import math\nfrom solution import stable_softmax\n\ndef test_shape_and_sum():\n    out = stable_softmax([2.0, 1.0, 0.1])\n    assert len(out) == 3\n    assert abs(sum(out) - 1.0) < 1e-9\n\ndef test_order():\n    out = stable_softmax([1.0, 2.0, 3.0])\n    assert out[2] > out[1] > out[0]\n\ndef test_large_logits_are_finite():\n    out = stable_softmax([1000.0, 1001.0, 1002.0])\n    assert all(math.isfinite(x) for x in out)\n    assert abs(sum(out) - 1.0) < 1e-9\n\ndef test_translation_invariance():\n    a = stable_softmax([1.0, 2.0, 3.0])\n    b = stable_softmax([101.0, 102.0, 103.0])\n    assert max(abs(x-y) for x,y in zip(a,b)) < 1e-9\n""",
    ),
    "week08": CodeChallenge(
        "rag-top-k",
        "week08",
        "RAG Top-K 检索",
        "RAG Top-K Retrieval",
        "实现 select_top_k(chunks, k)。chunks 是包含 id 与 score 的字典列表。按 score 降序返回前 k 个 id；分数相同时按 id 字符串升序，且不要修改输入。",
        "Implement select_top_k(chunks, k). chunks is a list of dicts containing id and score. Return the top-k ids by descending score, breaking ties by ascending id, without mutating the input.",
        """def select_top_k(chunks, k):\n    # TODO\n    raise NotImplementedError\n""",
        """from solution import select_top_k\n\ndef test_basic():\n    rows=[{'id':'a','score':0.2},{'id':'b','score':0.9},{'id':'c','score':0.5}]\n    assert select_top_k(rows,2)==['b','c']\n\ndef test_tie_break():\n    rows=[{'id':'b','score':0.8},{'id':'a','score':0.8},{'id':'c','score':0.1}]\n    assert select_top_k(rows,2)==['a','b']\n\ndef test_k_larger_than_input():\n    assert select_top_k([{'id':'x','score':1.0}],5)==['x']\n\ndef test_input_not_mutated():\n    rows=[{'id':'a','score':0.1},{'id':'b','score':0.2}]\n    before=[dict(x) for x in rows]\n    select_top_k(rows,1)\n    assert rows==before\n""",
    ),
    "week11": CodeChallenge(
        "agent-stop-guard",
        "week11",
        "Agent 循环停止条件",
        "Agent Loop Stop Guard",
        "实现 should_stop(step, max_steps, repeat_count, no_progress_count)。当达到最大步骤、重复次数 >=3、或连续无进展次数 >=2 时返回 True，否则 False。",
        "Implement should_stop(step, max_steps, repeat_count, no_progress_count). Return True when max steps are reached, repeats >=3, or no-progress count >=2; otherwise False.",
        """def should_stop(step, max_steps, repeat_count, no_progress_count):\n    # TODO\n    raise NotImplementedError\n""",
        """from solution import should_stop\n\ndef test_normal_progress():\n    assert should_stop(2,10,0,0) is False\n\ndef test_max_steps():\n    assert should_stop(10,10,0,0) is True\n\ndef test_repeat_guard():\n    assert should_stop(2,10,3,0) is True\n\ndef test_no_progress_guard():\n    assert should_stop(2,10,0,2) is True\n\ndef test_thresholds_not_reached():\n    assert should_stop(9,10,2,1) is False\n""",
    ),
    "week18": CodeChallenge(
        "coding-agent-next-action",
        "week18",
        "Coding Agent 状态决策",
        "Coding Agent State Decision",
        "实现 next_action(state)。规则：failed_tests>0 → 'fix'；有 changed_files 且 tests_run=False → 'test'；tests_run=True 且 failed_tests=0 → 'review'；否则 → 'inspect'。",
        "Implement next_action(state). Rules: failed_tests>0 -> 'fix'; changed_files and tests_run=False -> 'test'; tests_run=True and failed_tests=0 -> 'review'; otherwise -> 'inspect'.",
        """def next_action(state):\n    # TODO\n    raise NotImplementedError\n""",
        """from solution import next_action\n\ndef test_failed_tests_first():\n    assert next_action({'failed_tests':2,'changed_files':['a.py'],'tests_run':True})=='fix'\n\ndef test_changed_needs_test():\n    assert next_action({'failed_tests':0,'changed_files':['a.py'],'tests_run':False})=='test'\n\ndef test_review_after_green_tests():\n    assert next_action({'failed_tests':0,'changed_files':['a.py'],'tests_run':True})=='review'\n\ndef test_inspect_initial_state():\n    assert next_action({'failed_tests':0,'changed_files':[],'tests_run':False})=='inspect'\n""",
    ),
}


def init_tables() -> None:
    with db.connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS code_attempts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_key TEXT NOT NULL,
                challenge_key TEXT NOT NULL,
                source_code TEXT NOT NULL,
                score_percent REAL NOT NULL DEFAULT 0,
                passed INTEGER NOT NULL DEFAULT 0,
                passed_tests INTEGER NOT NULL DEFAULT 0,
                total_tests INTEGER NOT NULL DEFAULT 0,
                stdout TEXT NOT NULL DEFAULT '',
                stderr TEXT NOT NULL DEFAULT '',
                reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_code_attempts_lesson ON code_attempts(lesson_key,id DESC);
            """
        )


init_tables()


def _lang(request: Request) -> str:
    return normalize_lang(request.query_params.get("lang") or request.cookies.get("lang"))


def _nav(request: Request, lang: str) -> dict[str, Any]:
    progress = db.all_progress()
    lessons = [{"key": x.key, "week": x.week, "title": title_for(x, lang), "progress": progress.get(x.key, {"status":"not_started","percent":0,"score":None})} for x in LESSONS]
    return {"request": request, "lang": lang, "t": lambda key: tr(lang,key), "lessons": lessons, "current_path": request.url.path}


def _attempts(lesson_key: str, limit: int = 10) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM code_attempts WHERE lesson_key=? ORDER BY id DESC LIMIT ?", (lesson_key, limit)).fetchall()
    return [dict(x) for x in rows]


@router.get("/coding-labs", response_class=HTMLResponse)
def coding_labs(request: Request):
    lang = _lang(request)
    items = []
    for lesson_key, challenge in CHALLENGES.items():
        history = _attempts(lesson_key, 100)
        items.append({"challenge": challenge, "lesson": LESSON_MAP[lesson_key], "title": challenge.en if lang == "en" else challenge.zh,
                      "attempt_count": len(history), "best": max((float(x["score_percent"]) for x in history), default=None)})
    c = _nav(request, lang); c["coding_items"] = items
    return templates.TemplateResponse(request=request, name="coding_labs.html", context=c)


@router.get("/coding-labs/{lesson_key}", response_class=HTMLResponse)
def coding_lab(request: Request, lesson_key: str):
    challenge = CHALLENGES.get(lesson_key)
    if not challenge:
        raise HTTPException(404)
    lang = _lang(request)
    c = _nav(request, lang)
    c.update({"challenge": challenge, "lesson": LESSON_MAP[lesson_key], "title": challenge.en if lang == "en" else challenge.zh,
              "prompt": challenge.prompt_en if lang == "en" else challenge.prompt_zh,
              "source": challenge.starter, "history": _attempts(lesson_key)})
    return templates.TemplateResponse(request=request, name="coding_lab.html", context=c)


@router.post("/coding-labs/{lesson_key}/run", response_class=HTMLResponse)
def run_coding_lab(request: Request, lesson_key: str, source_code: str = Form(...)):
    challenge = CHALLENGES.get(lesson_key)
    if not challenge:
        raise HTTPException(404)
    if len(source_code) > 20000:
        raise HTTPException(413, "Source code is too large")
    runner = get_code_runner()
    with tempfile.TemporaryDirectory(prefix="llm-learning-code-") as tmp:
        result = runner.run(CodeRunRequest(source_code=source_code, tests_source=challenge.tests), Path(tmp))
    passed = result.enabled and result.score_percent >= challenge.pass_score
    with db.connect() as conn:
        cur = conn.execute(
            """INSERT INTO code_attempts(lesson_key,challenge_key,source_code,score_percent,passed,passed_tests,total_tests,stdout,stderr,reason,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (lesson_key, challenge.key, source_code, result.score_percent, 1 if passed else 0, result.passed_tests, result.total_tests,
             result.stdout, result.stderr, result.reason, now_iso()),
        )
        attempt_id = int(cur.lastrowid)
    return RedirectResponse(f"/coding-labs/{lesson_key}/result/{attempt_id}", status_code=303)


@router.get("/coding-labs/{lesson_key}/result/{attempt_id}", response_class=HTMLResponse)
def coding_result(request: Request, lesson_key: str, attempt_id: int):
    challenge = CHALLENGES.get(lesson_key)
    if not challenge:
        raise HTTPException(404)
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM code_attempts WHERE id=? AND lesson_key=?", (attempt_id, lesson_key)).fetchone()
    if not row:
        raise HTTPException(404)
    lang = _lang(request); c = _nav(request, lang)
    c.update({"challenge": challenge, "lesson": LESSON_MAP[lesson_key], "title": challenge.en if lang == "en" else challenge.zh,
              "result": dict(row)})
    return templates.TemplateResponse(request=request, name="coding_result.html", context=c)

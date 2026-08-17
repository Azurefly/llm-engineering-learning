from __future__ import annotations

import json
import secrets
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .code_exam import CHALLENGES
from .course import LESSONS, LESSON_MAP, title_for
from .exam_system import Question
from .exam_v2 import (
    QUESTION_INDEX,
    WEEK_TAGS,
    _choose_balanced,
    _lang,
    _latest_question_state,
    _nav,
    bank_for,
    db,
    knowledge_for,
    templates,
)
from .exam_v3 import _create_runtime_attempt

router = APIRouter()


@dataclass(frozen=True)
class Domain:
    key: str
    weeks: tuple[str, ...]
    zh: str
    en: str


DOMAINS: tuple[Domain, ...] = (
    Domain("foundation", tuple(f"week{i:02d}" for i in range(0, 5)), "基础原理", "Foundations"),
    Domain("llm_app", tuple(f"week{i:02d}" for i in range(5, 8)), "LLM 应用", "LLM Apps"),
    Domain("rag", tuple(f"week{i:02d}" for i in range(8, 11)), "RAG 工程", "RAG"),
    Domain("agent", tuple(f"week{i:02d}" for i in range(11, 14)), "Agent 工程", "Agents"),
    Domain("platform", tuple(f"week{i:02d}" for i in range(14, 17)), "平台治理", "Platform"),
    Domain("advanced", tuple(f"week{i:02d}" for i in range(17, 19)), "进阶工程", "Advanced"),
)


def _status(score: float, evidence_count: int) -> str:
    if evidence_count <= 0:
        return "unseen"
    if score < 40:
        return "weak"
    if score < 70:
        return "developing"
    if score < 85:
        return "proficient"
    return "mastered"


def _mastery_from_evidence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert newest-first evidence into a transparent recency-weighted score."""
    if not rows:
        return {
            "score": 0.0,
            "status": "unseen",
            "evidence_count": 0,
            "confidence": 0.0,
            "wrong_count": 0,
            "priority": 0.0,
        }
    samples = rows[:10]
    weighted = 0.0
    weights = 0.0
    for index, item in enumerate(samples):
        recency = max(0.35, 1.0 - index * 0.08)
        source_weight = float(item.get("source_weight") or 1.0)
        weight = recency * source_weight
        weighted += float(item.get("score") or 0.0) * weight
        weights += weight
    score = round(weighted / weights, 1) if weights else 0.0
    count = len(rows)
    confidence = round(min(1.0, count / 5.0), 2)
    wrong_count = sum(1 for item in rows if float(item.get("score") or 0.0) < 70)
    priority = round((100.0 - score) * (0.65 + 0.35 * confidence) + min(10, wrong_count * 1.5), 1)
    return {
        "score": score,
        "status": _status(score, count),
        "evidence_count": count,
        "confidence": confidence,
        "wrong_count": wrong_count,
        "priority": priority,
    }


def _exam_evidence() -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT a.id AS attempt_id,a.submitted_at,ea.question_id,ea.earned,ea.max_points,ea.correct,
                      aq.lesson_key,aq.knowledge_json
               FROM exam_answers ea
               JOIN exam_attempts a ON a.id=ea.attempt_id
               LEFT JOIN exam_attempt_questions aq
                 ON aq.attempt_id=ea.attempt_id AND aq.question_id=ea.question_id
               WHERE a.status='submitted'
               ORDER BY a.id DESC,ea.id DESC"""
        ).fetchall()
    result: list[dict[str, Any]] = []
    for raw in rows:
        item = dict(raw)
        lesson_key = item.get("lesson_key")
        indexed = QUESTION_INDEX.get(item["question_id"])
        if not lesson_key and indexed:
            lesson_key = indexed[0]
        tags: tuple[str, ...] = ()
        if item.get("knowledge_json"):
            try:
                parsed = json.loads(item["knowledge_json"])
                tags = tuple(str(x) for x in parsed if str(x).strip())
            except (TypeError, json.JSONDecodeError):
                tags = ()
        if not tags and indexed and lesson_key:
            tags = knowledge_for(lesson_key, indexed[1])
        max_points = float(item.get("max_points") or 0)
        score = round(float(item.get("earned") or 0) / max_points * 100, 2) if max_points else 0.0
        result.append(
            {
                "lesson_key": lesson_key,
                "tags": tags,
                "score": score,
                "timestamp": item.get("submitted_at") or "",
                "source": "exam",
                "source_weight": 1.0,
                "question_id": item["question_id"],
            }
        )
    return result


def _code_evidence() -> list[dict[str, Any]]:
    with db.connect() as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "code_attempts" not in tables:
            return []
        rows = conn.execute(
            "SELECT id,lesson_key,score_percent,created_at FROM code_attempts ORDER BY id DESC"
        ).fetchall()
    result: list[dict[str, Any]] = []
    for raw in rows:
        item = dict(raw)
        lesson_key = item["lesson_key"]
        result.append(
            {
                "lesson_key": lesson_key,
                "tags": WEEK_TAGS.get(lesson_key, ()),
                "score": float(item.get("score_percent") or 0),
                "timestamp": item.get("created_at") or "",
                "source": "code",
                "source_weight": 1.25,
                "question_id": f"code:{lesson_key}:{item['id']}",
            }
        )
    return result


def mastery_profile() -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    tag_weeks: dict[str, set[str]] = defaultdict(set)
    for lesson_key, tags in WEEK_TAGS.items():
        for tag in tags:
            tag_weeks[tag].add(lesson_key)
    for item in _exam_evidence() + _code_evidence():
        for tag in item.get("tags") or ():
            grouped[str(tag)].append(item)
            if item.get("lesson_key"):
                tag_weeks[str(tag)].add(str(item["lesson_key"]))
    profile: dict[str, dict[str, Any]] = {}
    for tag in sorted(set(tag_weeks) | set(grouped)):
        rows = sorted(grouped.get(tag, []), key=lambda x: x.get("timestamp") or "", reverse=True)
        summary = _mastery_from_evidence(rows)
        summary.update({"tag": tag, "weeks": sorted(tag_weeks.get(tag, set()))})
        profile[tag] = summary
    return profile


def domain_profile(profile: dict[str, dict[str, Any]], lang: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for domain in DOMAINS:
        tags = {tag for week in domain.weeks for tag in WEEK_TAGS.get(week, ())}
        values = [profile[tag] for tag in tags if tag in profile and profile[tag]["evidence_count"] > 0]
        if values:
            denom = sum(max(0.2, float(x["confidence"])) for x in values)
            score = round(sum(float(x["score"]) * max(0.2, float(x["confidence"])) for x in values) / denom, 1)
            evidence_count = sum(int(x["evidence_count"]) for x in values)
        else:
            score = 0.0
            evidence_count = 0
        result.append(
            {
                "key": domain.key,
                "label": domain.en if lang == "en" else domain.zh,
                "score": score,
                "status": _status(score, evidence_count),
                "evidence_count": evidence_count,
            }
        )
    return result


def recommendations(profile: dict[str, dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    progress = db.all_progress()
    candidates = [x for x in profile.values() if x["status"] in {"weak", "developing"}]
    candidates.sort(key=lambda x: (x["priority"], -x["score"]), reverse=True)
    result: list[dict[str, Any]] = []
    for item in candidates[:limit]:
        weeks = [w for w in item["weeks"] if w in LESSON_MAP]
        if not weeks:
            continue
        weeks.sort(key=lambda w: (int(progress.get(w, {}).get("percent") or 0), LESSON_MAP[w].week))
        lesson_key = weeks[0]
        result.append({**item, "lesson_key": lesson_key, "lesson": LESSON_MAP[lesson_key]})
    return result


def recent_assessments(limit: int = 20) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with db.connect() as conn:
        exam_rows = conn.execute(
            """SELECT a.id,a.lesson_key,a.percent,a.submitted_at,m.mode,m.scope_key
               FROM exam_attempts a LEFT JOIN exam_v2_meta m ON m.attempt_id=a.id
               WHERE a.status='submitted' ORDER BY a.id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        code_rows = []
        if "code_attempts" in tables:
            code_rows = conn.execute(
                "SELECT id,lesson_key,score_percent,created_at FROM code_attempts ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    for raw in exam_rows:
        item = dict(raw)
        lesson_key = item.get("scope_key") if item.get("mode") == "weekly" else item.get("lesson_key")
        label = lesson_key.replace("week", "W") if isinstance(lesson_key, str) else "Exam"
        events.append({"kind": "exam", "label": label, "score": round(float(item.get("percent") or 0), 1), "at": item.get("submitted_at") or ""})
    for raw in code_rows:
        item = dict(raw)
        events.append({"kind": "code", "label": item["lesson_key"].replace("week", "W") + " Code", "score": round(float(item.get("score_percent") or 0), 1), "at": item.get("created_at") or ""})
    events.sort(key=lambda x: x["at"])
    return events[-limit:]


def _overall(profile: dict[str, dict[str, Any]]) -> float:
    values = [x for x in profile.values() if x["evidence_count"] > 0]
    if not values:
        return 0.0
    denom = sum(max(0.2, float(x["confidence"])) for x in values)
    return round(sum(float(x["score"]) * max(0.2, float(x["confidence"])) for x in values) / denom, 1)


def _review_pool(profile: dict[str, dict[str, Any]], knowledge: str | None = None) -> list[tuple[str, Question]]:
    if knowledge:
        targets = {knowledge}
    else:
        targets = {tag for tag, item in profile.items() if item["status"] in {"weak", "developing"}}
    pool: list[tuple[str, Question]] = []
    for lesson in LESSONS:
        for question in bank_for(lesson.key):
            tags = set(knowledge_for(lesson.key, question))
            if tags & targets:
                pool.append((lesson.key, question))
    if pool:
        return pool
    return [(item["lesson_key"], item["question"]) for item in _latest_question_state()]


@router.get("/adaptive", response_class=HTMLResponse)
def adaptive_dashboard(request: Request):
    lang = _lang(request)
    profile = mastery_profile()
    domains = domain_profile(profile, lang)
    recs = recommendations(profile)
    mastery_items = sorted(profile.values(), key=lambda x: (x["status"] == "unseen", -x["priority"], x["tag"]))
    distribution = {key: sum(1 for x in profile.values() if x["status"] == key) for key in ("weak", "developing", "proficient", "mastered", "unseen")}
    c = _nav(request, lang)
    c.update(
        {
            "overall": _overall(profile),
            "domains": domains,
            "mastery_items": mastery_items,
            "recommendations": recs,
            "trend": recent_assessments(),
            "distribution": distribution,
            "evidence_total": sum(int(x["evidence_count"]) for x in profile.values()),
            "coding_count": len(CHALLENGES),
        }
    )
    return templates.TemplateResponse(request=request, name="adaptive.html", context=c)


@router.post("/adaptive/review/start")
def start_adaptive_review(request: Request, knowledge: str | None = Form(default=None)):
    lang = _lang(request)
    profile = mastery_profile()
    pool = _review_pool(profile, knowledge.strip() if knowledge else None)
    if not pool:
        return RedirectResponse("/adaptive?review=empty", status_code=303)
    seed = secrets.randbits(31)
    selected = _choose_balanced(pool, min(10, len(pool)), seed)
    subject = knowledge.strip() if knowledge else None
    title_zh = f"{subject} 自适应复习" if subject else "薄弱知识点自适应复习"
    title_en = f"Adaptive Review · {subject}" if subject else "Adaptive Weakness Review"
    attempt_id = _create_runtime_attempt(
        lesson_key="adaptive",
        lang=lang,
        mode="adaptive",
        scope_key=subject or "weakness",
        title_zh=title_zh,
        title_en=title_en,
        selected=selected,
        pass_score=80,
        seed=seed,
    )
    return RedirectResponse(f"/exam-v2/attempt/{attempt_id}", status_code=303)

from __future__ import annotations

import re
import sys
from typing import Any

from . import exam_system
from .exam_system import Question

_ORIGINAL_GRADE_QUESTION = exam_system.grade_question
_CJK = re.compile(r"[\u3400-\u9fff]")


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def contains_rubric_term(answer: str, term: str) -> bool:
    """Match CJK phrases naturally and Latin technical terms on token boundaries."""
    value = _norm(answer)
    wanted = _norm(term)
    if not wanted:
        return False
    if _CJK.search(wanted):
        return wanted in value
    # Short technical acronyms such as RAG/MCP/SFT must not match inside words
    # such as "storage" or arbitrary identifier fragments.
    pattern = rf"(?<![a-z0-9_]){re.escape(wanted)}(?![a-z0-9_])"
    return re.search(pattern, value, flags=re.IGNORECASE) is not None


def grade_question_strict(q: Question, answer: Any) -> dict[str, Any]:
    if q.kind != "short":
        return _ORIGINAL_GRADE_QUESTION(q, answer)
    value = _norm(str(answer or ""))
    matched: list[str] = []
    missing: list[str] = []
    for group in q.concepts:
        target = matched if any(contains_rubric_term(value, term) for term in group) else missing
        target.append(group[0])
    earned = round(q.points * len(matched) / len(q.concepts), 2) if q.concepts else 0.0
    return {
        "question_id": q.id,
        "earned": float(earned),
        "max_points": q.points,
        "correct": float(earned) == q.points,
        "matched": matched,
        "missing": missing,
    }


def install() -> None:
    exam_system.grade_question = grade_question_strict
    for module_name in ("app.exam_v2", "app.adaptive_v5"):
        module = sys.modules.get(module_name)
        if module is not None and hasattr(module, "grade_question"):
            setattr(module, "grade_question", grade_question_strict)


install()

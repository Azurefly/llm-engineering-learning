from __future__ import annotations

from typing import Any

from .course import LESSONS
from .exam_v2 import bank_for, difficulty_for, knowledge_for

MIN_QUESTIONS_PER_WEEK = 9


def validate_question_bank() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    weeks: list[dict[str, Any]] = []

    for lesson in LESSONS:
        questions = bank_for(lesson.key)
        difficulties = {"easy": 0, "medium": 0, "hard": 0}
        prompts: set[tuple[str, str]] = set()
        for q in questions:
            if q.id in seen_ids:
                errors.append(f"duplicate question id: {q.id}")
            seen_ids.add(q.id)
            if not q.zh.strip() or not q.en.strip():
                errors.append(f"{q.id}: missing bilingual prompt")
            normalized_prompt = (" ".join(q.zh.lower().split()), " ".join(q.en.lower().split()))
            if normalized_prompt in prompts:
                errors.append(f"{q.id}: duplicate prompt in {lesson.key}")
            prompts.add(normalized_prompt)
            difficulties[difficulty_for(q)] += 1
            if not knowledge_for(lesson.key, q):
                errors.append(f"{q.id}: missing knowledge tag")
            if q.kind in {"single", "multiple"}:
                values = [str(x[0]) for x in q.options]
                if len(values) < 2 or len(values) != len(set(values)):
                    errors.append(f"{q.id}: invalid or duplicate option values")
                wanted = {str(q.answer)} if q.kind == "single" else {str(x) for x in (q.answer or ())}
                if not wanted or not wanted.issubset(set(values)):
                    errors.append(f"{q.id}: answer is not covered by options")
            elif q.kind == "fill" and not q.accepted:
                errors.append(f"{q.id}: fill question has no accepted answers")
            elif q.kind == "short" and len(q.concepts) < 2:
                errors.append(f"{q.id}: short question needs at least two rubric concepts")

        if len(questions) < MIN_QUESTIONS_PER_WEEK:
            errors.append(f"{lesson.key}: only {len(questions)} questions; minimum is {MIN_QUESTIONS_PER_WEEK}")
        if difficulties["medium"] == 0:
            warnings.append(f"{lesson.key}: no medium questions")
        if difficulties["hard"] == 0:
            warnings.append(f"{lesson.key}: no hard questions")
        weeks.append({"lesson_key": lesson.key, "count": len(questions), "difficulty": difficulties})

    return {"ok": not errors, "errors": errors, "warnings": warnings, "total": len(seen_ids), "weeks": weeks}

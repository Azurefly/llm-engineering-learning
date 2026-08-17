from __future__ import annotations

from . import exam_v2
from .question_bank_v5 import APPLICATION_QUESTIONS


def install() -> None:
    for lesson_key, questions in APPLICATION_QUESTIONS.items():
        existing = list(exam_v2.EXTRA_QUESTIONS.get(lesson_key, ()))
        known = {q.id for q in existing}
        for question in questions:
            if question.id not in known:
                existing.append(question)
                known.add(question.id)
            exam_v2.QUESTION_INDEX[question.id] = (lesson_key, question)
        exam_v2.EXTRA_QUESTIONS[lesson_key] = tuple(existing)


install()

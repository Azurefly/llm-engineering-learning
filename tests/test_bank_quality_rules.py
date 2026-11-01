"""The question-bank validator must reject every malformed question shape."""

import dataclasses

import pytest

from app import bank_quality
from app.exam_system import Question


def _question(**overrides) -> Question:
    base = {
        "id": "probe-1",
        "kind": "single",
        "points": 1.0,
        "zh": "问题",
        "en": "question",
        "options": (("a", "甲", "A"), ("b", "乙", "B")),
        "answer": "a",
        "accepted": (),
        "concepts": (),
    }
    base.update(overrides)
    return Question(**base)


def _validate(monkeypatch, questions, *, knowledge=("tag",), difficulty="easy"):
    # The validator walks every lesson, so give each lesson its own id namespace
    # while keeping prompt/option shapes intact.
    monkeypatch.setattr(
        bank_quality,
        "bank_for",
        lambda key: [dataclasses.replace(question, id=f"{question.id}@{key}") for question in questions],
    )
    monkeypatch.setattr(bank_quality, "knowledge_for", lambda key, q: knowledge)
    monkeypatch.setattr(bank_quality, "difficulty_for", lambda q: difficulty)
    return bank_quality.validate_question_bank()


def _errors(report) -> str:
    return "\n".join(report["errors"])


def test_duplicate_question_ids_are_rejected(monkeypatch):
    report = _validate(monkeypatch, [_question(), _question()])
    assert "duplicate question id" in _errors(report)
    assert report["ok"] is False


def test_missing_bilingual_prompt_is_rejected(monkeypatch):
    report = _validate(monkeypatch, [_question(zh="   ")])
    assert "missing bilingual prompt" in _errors(report)


def test_duplicate_prompt_within_a_week_is_rejected(monkeypatch):
    first = _question(id="probe-1")
    second = _question(id="probe-2")
    report = _validate(monkeypatch, [first, second])
    assert "duplicate prompt" in _errors(report)


def test_missing_knowledge_tag_is_rejected(monkeypatch):
    report = _validate(monkeypatch, [_question()], knowledge=())
    assert "missing knowledge tag" in _errors(report)


def test_single_choice_needs_at_least_two_options(monkeypatch):
    report = _validate(monkeypatch, [_question(options=(("a", "甲", "A"),))])
    assert "invalid or duplicate option values" in _errors(report)


def test_duplicate_option_values_are_rejected(monkeypatch):
    report = _validate(monkeypatch, [_question(options=(("a", "甲", "A"), ("a", "乙", "B")))])
    assert "invalid or duplicate option values" in _errors(report)


def test_answer_outside_the_options_is_rejected(monkeypatch):
    report = _validate(monkeypatch, [_question(answer="z")])
    assert "answer is not covered by options" in _errors(report)


def test_multi_select_answer_must_be_covered_by_options(monkeypatch):
    report = _validate(monkeypatch, [_question(kind="multiple", answer=("a", "z"))])
    assert "answer is not covered by options" in _errors(report)


def test_fill_question_without_accepted_answers_is_rejected(monkeypatch):
    report = _validate(monkeypatch, [_question(kind="fill", options=(), answer=None)])
    assert "fill question has no accepted answers" in _errors(report)


def test_short_question_needs_two_rubric_concepts(monkeypatch):
    report = _validate(monkeypatch, [_question(kind="short", options=(), answer=None, concepts=(("only",),))])
    assert "needs at least two rubric concepts" in _errors(report)


def test_weeks_below_the_minimum_question_count_are_rejected(monkeypatch):
    report = _validate(monkeypatch, [])
    assert "minimum is" in _errors(report)


def test_weeks_without_medium_or_hard_questions_raise_warnings(monkeypatch):
    questions = [
        _question(id=f"probe-{i}", zh=f"问题 {i}", en=f"question {i}")
        for i in range(bank_quality.MIN_QUESTIONS_PER_WEEK)
    ]
    report = _validate(monkeypatch, questions, difficulty="easy")

    assert report["ok"] is True
    assert any("no medium questions" in warning for warning in report["warnings"])
    assert any("no hard questions" in warning for warning in report["warnings"])


@pytest.mark.parametrize("kind", ["single", "multiple", "fill", "short"])
def test_valid_questions_of_every_kind_pass(monkeypatch, kind):
    if kind == "single":
        question = _question(kind="single")
    elif kind == "multiple":
        question = _question(kind="multiple", answer=("a", "b"))
    elif kind == "fill":
        question = _question(kind="fill", options=(), answer=None, accepted=("x",))
    else:
        question = _question(kind="short", options=(), answer=None, concepts=(("one",), ("two",)))

    questions = [
        dataclasses.replace(question, id=f"{kind}-{i}", zh=f"问题 {i}", en=f"question {i}")
        for i in range(bank_quality.MIN_QUESTIONS_PER_WEEK)
    ]
    report = _validate(monkeypatch, questions)

    assert report["ok"] is True, _errors(report)

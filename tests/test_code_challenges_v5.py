from app.current import app  # noqa: F401
from app.code_exam import CHALLENGES


def test_every_engineering_week_has_a_coding_lab():
    expected = {f"week{i:02d}" for i in range(2, 19)}
    assert expected.issubset(CHALLENGES.keys())


def test_coding_lab_sources_compile_and_are_bilingual():
    for lesson_key in sorted(f"week{i:02d}" for i in range(2, 19)):
        challenge = CHALLENGES[lesson_key]
        assert challenge.zh.strip() and challenge.en.strip()
        assert challenge.prompt_zh.strip() and challenge.prompt_en.strip()
        compile(challenge.starter, f"{lesson_key}-starter.py", "exec")
        compile(challenge.tests, f"{lesson_key}-tests.py", "exec")
        assert 1 <= challenge.pass_score <= 100

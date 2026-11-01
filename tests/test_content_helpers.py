"""Fallbacks for lesson content loading and workspace search helpers."""

from app.course import LESSONS, _extract_week_section, load_lesson_markdown
from app.search import _snippet, search_workspace

DETAILED = LESSONS[0]  # week00 ships a dedicated markdown file
ROADMAP_ONLY = LESSONS[3]  # week03+ live inside the roadmap


def test_extract_week_section_returns_the_whole_text_when_the_week_is_absent():
    text = "# Week 7 — something\n\nbody"
    assert _extract_week_section(text, 3) == text


def test_extract_week_section_stops_at_the_next_week():
    text = "# Week 1 — a\n\nfirst body\n\n# Week 2 — b\n\nsecond body\n"
    section = _extract_week_section(text, 1)
    assert "first body" in section
    assert "second body" not in section


def test_load_lesson_markdown_prefers_the_detail_file(tmp_path):
    target = tmp_path / DETAILED.detail_zh
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# detail body", encoding="utf-8")

    text, source = load_lesson_markdown(tmp_path, DETAILED, "zh-CN")

    assert text == "# detail body"
    assert source == DETAILED.detail_zh


def test_load_lesson_markdown_falls_back_to_the_roadmap_section(tmp_path):
    (tmp_path / "ROADMAP.md").write_text(
        f"# Week {ROADMAP_ONLY.week} — roadmap title\n\nroadmap body\n\n"
        f"# Week {ROADMAP_ONLY.week + 1} — next\n\nnext body\n",
        encoding="utf-8",
    )

    text, source = load_lesson_markdown(tmp_path, ROADMAP_ONLY, "zh-CN")

    assert "roadmap body" in text
    assert "next body" not in text
    assert source == "ROADMAP.md"


def test_load_lesson_markdown_reports_a_placeholder_when_nothing_exists(tmp_path):
    text, source = load_lesson_markdown(tmp_path, ROADMAP_ONLY, "en")

    assert "being prepared" in text
    assert source == ""


def test_snippet_returns_a_prefix_when_the_query_is_absent():
    snippet = _snippet("alpha beta gamma", "missing", width=5)
    assert snippet == "alpha"


def test_snippet_marks_a_truncated_window_with_ellipses():
    snippet = _snippet("x" * 400 + "needle" + "y" * 400, "needle", width=40)
    assert "needle" in snippet
    assert snippet.startswith("…")
    assert snippet.endswith("…")


def test_search_workspace_ignores_queries_that_are_too_short():
    assert search_workspace("", "zh-CN") == []
    assert search_workspace("  a  ", "zh-CN") == []


def test_search_workspace_finds_a_lesson_by_title():
    results = search_workspace("Transformer", "zh-CN")
    course_hits = [item for item in results if item["kind"] == "course"]
    assert course_hits
    assert any(item["url"] == "/course/week04" for item in course_hits)

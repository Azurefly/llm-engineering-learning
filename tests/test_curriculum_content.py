from pathlib import Path

from app.course import LESSONS, load_lesson_markdown

ROOT = Path(__file__).resolve().parents[1]


def test_every_week_has_non_placeholder_bilingual_content():
    placeholders = ('详细课程内容正在补充', 'Detailed lesson content is being prepared')
    for lesson in LESSONS:
        for lang in ('zh-CN', 'en'):
            text, source = load_lesson_markdown(ROOT, lesson, lang)
            assert source, f'{lesson.key} {lang} has no content source'
            assert len(text.strip()) >= 200, f'{lesson.key} {lang} content is too short'
            assert not any(marker in text for marker in placeholders), f'{lesson.key} {lang} is still placeholder content'
            assert f'Week {lesson.week}' in text or lesson.week == 0, f'{lesson.key} {lang} is not mapped to the expected week'

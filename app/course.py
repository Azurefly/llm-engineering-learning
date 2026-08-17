from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class Lesson:
    key: str
    week: int
    title_zh: str
    title_en: str
    detail_zh: str | None = None
    detail_en: str | None = None


LESSONS = [
    Lesson("week00", 0, "基线测试", "Baseline Assessment", "docs/00-baseline-test.md", "docs/00-baseline-test.en.md"),
    Lesson("week01", 1, "数学与机器学习基础", "Math & Machine Learning Foundations", "docs/week01-ml-foundations.md", "docs/week01-ml-foundations.en.md"),
    Lesson("week02", 2, "神经网络与 PyTorch", "Neural Networks & PyTorch", "docs/week02-neural-network-pytorch.md", "docs/week02-neural-network-pytorch.en.md"),
    Lesson("week03", 3, "Tokenizer 与语言模型", "Tokenizers & Language Modeling"),
    Lesson("week04", 4, "Transformer / Attention", "Transformer / Attention"),
    Lesson("week05", 5, "LLM API 与 Prompt Engineering", "LLM APIs & Prompt Engineering"),
    Lesson("week06", 6, "Structured Output / Tool Calling", "Structured Output / Tool Calling"),
    Lesson("week07", 7, "Embedding / Vector DB", "Embeddings / Vector Databases"),
    Lesson("week08", 8, "基础 RAG", "Basic RAG"),
    Lesson("week09", 9, "高级 RAG", "Advanced RAG"),
    Lesson("week10", 10, "RAG Evaluation", "RAG Evaluation"),
    Lesson("week11", 11, "Agent 基础", "Agent Foundations"),
    Lesson("week12", 12, "Agent Runtime / Guardrails", "Agent Runtime / Guardrails"),
    Lesson("week13", 13, "MCP", "MCP"),
    Lesson("week14", 14, "LiteLLM / Model Router", "LiteLLM / Model Router"),
    Lesson("week15", 15, "Evaluation / Observability / Security", "Evaluation / Observability / Security"),
    Lesson("week16", 16, "本地模型与推理部署", "Local Models & Inference Deployment"),
    Lesson("week17", 17, "Fine-tuning / LoRA", "Fine-tuning / LoRA"),
    Lesson("week18", 18, "Coding Agent 毕业项目", "Coding Agent Capstone"),
]

LESSON_MAP = {lesson.key: lesson for lesson in LESSONS}


def title_for(lesson: Lesson, lang: str) -> str:
    return lesson.title_en if lang == "en" else lesson.title_zh


def _extract_week_section(text: str, week: int) -> str:
    pattern = re.compile(
        rf"(?ms)^#\s+Week\s+{week}\b.*?(?=^#\s+Week\s+{week + 1}\b|\Z)"
    )
    match = pattern.search(text)
    if match:
        return match.group(0).strip()
    return text


def load_lesson_markdown(repo_root: Path, lesson: Lesson, lang: str) -> tuple[str, str]:
    detail = lesson.detail_en if lang == "en" else lesson.detail_zh
    if detail:
        path = repo_root / detail
        if path.exists():
            return path.read_text(encoding="utf-8"), detail

    roadmap_name = "ROADMAP.en.md" if lang == "en" else "ROADMAP.md"
    roadmap_path = repo_root / roadmap_name
    if roadmap_path.exists():
        section = _extract_week_section(roadmap_path.read_text(encoding="utf-8"), lesson.week)
        return section, roadmap_name

    fallback = (
        f"# Week {lesson.week} — {title_for(lesson, lang)}\n\n"
        + ("Detailed lesson content is being prepared." if lang == "en" else "详细课程内容正在补充。")
    )
    return fallback, ""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class CodeRunRequest:
    source_code: str
    language: str = "python"
    test_command: tuple[str, ...] = ("pytest", "-q")
    timeout_seconds: int = 20


@dataclass(frozen=True)
class CodeRunResult:
    enabled: bool
    passed: bool
    score_percent: float
    exit_code: int | None
    stdout: str
    stderr: str
    reason: str = ""


class CodeRunner(Protocol):
    """Execution boundary for future coding-exam grading.

    Implementations must run untrusted learner code in an isolated environment.
    The default application intentionally does not execute arbitrary code.
    """

    def run(self, request: CodeRunRequest, workspace: Path) -> CodeRunResult:
        ...


class DisabledCodeRunner:
    """Safe default until an isolated container/sandbox runner is configured."""

    def run(self, request: CodeRunRequest, workspace: Path) -> CodeRunResult:
        return CodeRunResult(
            enabled=False,
            passed=False,
            score_percent=0.0,
            exit_code=None,
            stdout="",
            stderr="",
            reason=(
                "Code execution is disabled. Configure a sandboxed runner "
                "before enabling coding exams."
            ),
        )

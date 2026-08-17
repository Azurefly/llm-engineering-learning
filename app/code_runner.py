from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class CodeRunRequest:
    source_code: str
    tests_source: str
    language: str = "python"
    filename: str = "solution.py"
    test_filename: str = "test_solution.py"
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
    passed_tests: int = 0
    total_tests: int = 0


class CodeRunner(Protocol):
    """Execution boundary for untrusted learner code."""

    def run(self, request: CodeRunRequest, workspace: Path) -> CodeRunResult:
        ...


class DisabledCodeRunner:
    """Safe default. Arbitrary learner code is never executed unless explicitly enabled."""

    def run(self, request: CodeRunRequest, workspace: Path) -> CodeRunResult:
        return CodeRunResult(
            enabled=False,
            passed=False,
            score_percent=0.0,
            exit_code=None,
            stdout="",
            stderr="",
            reason=(
                "Code execution is disabled. Set LLM_CODE_RUNNER=docker and build "
                "the sandbox image before enabling coding exams."
            ),
        )


class DockerSandboxCodeRunner:
    """Run learner Python in a disposable, network-disabled Docker sandbox.

    The sandbox container receives only a read-only temporary workspace. It has no
    network, no extra Linux capabilities, a PID/memory/CPU limit, a read-only root
    filesystem, and a small tmpfs. The application must itself be able to invoke
    the Docker CLI. This is intended for a trusted local workstation, not a public
    multi-tenant judge.
    """

    def __init__(self, image: str | None = None, docker_bin: str | None = None):
        self.image = image or os.getenv("LLM_CODE_RUNNER_IMAGE", "llm-learning-sandbox:py312")
        self.docker_bin = docker_bin or shutil.which("docker") or "docker"

    def build_command(self, workspace: Path, test_filename: str) -> list[str]:
        return [
            self.docker_bin,
            "run",
            "--rm",
            "--network",
            "none",
            "--memory",
            "128m",
            "--cpus",
            "0.50",
            "--pids-limit",
            "64",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            "-v",
            f"{workspace.resolve()}:/workspace:ro",
            "-w",
            "/workspace",
            self.image,
            test_filename,
        ]

    @staticmethod
    def _score(stdout: str, stderr: str, exit_code: int) -> tuple[int, int, float]:
        text = f"{stdout}\n{stderr}"
        passed = sum(int(x) for x in re.findall(r"(\d+) passed", text))
        failed = sum(int(x) for x in re.findall(r"(\d+) failed", text))
        errors = sum(int(x) for x in re.findall(r"(\d+) error(?:s)?", text))
        total = passed + failed + errors
        if exit_code == 0 and total == 0:
            return 1, 1, 100.0
        if total == 0:
            return 0, 0, 0.0
        return passed, total, round(passed / total * 100, 2)

    def run(self, request: CodeRunRequest, workspace: Path) -> CodeRunResult:
        if request.language != "python":
            return CodeRunResult(False, False, 0.0, None, "", "", "Only Python is supported in V3.")
        if shutil.which(self.docker_bin) is None and not Path(self.docker_bin).exists():
            return CodeRunResult(False, False, 0.0, None, "", "", "Docker CLI was not found.")

        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / request.filename).write_text(request.source_code, encoding="utf-8")
        (workspace / request.test_filename).write_text(request.tests_source, encoding="utf-8")
        command = self.build_command(workspace, request.test_filename)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=max(1, min(int(request.timeout_seconds), 60)),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return CodeRunResult(
                True,
                False,
                0.0,
                None,
                exc.stdout or "",
                exc.stderr or "",
                "Sandbox execution timed out.",
            )
        except OSError as exc:
            return CodeRunResult(True, False, 0.0, None, "", str(exc), "Failed to start Docker sandbox.")

        passed_tests, total_tests, score = self._score(completed.stdout, completed.stderr, completed.returncode)
        return CodeRunResult(
            enabled=True,
            passed=completed.returncode == 0,
            score_percent=score,
            exit_code=completed.returncode,
            stdout=completed.stdout[-12000:],
            stderr=completed.stderr[-12000:],
            passed_tests=passed_tests,
            total_tests=total_tests,
        )


def get_code_runner() -> CodeRunner:
    if os.getenv("LLM_CODE_RUNNER", "disabled").strip().lower() == "docker":
        return DockerSandboxCodeRunner()
    return DisabledCodeRunner()

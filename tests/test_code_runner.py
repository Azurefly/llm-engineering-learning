import subprocess
from pathlib import Path

import pytest

from app import code_runner
from app.code_runner import (
    CodeRunRequest,
    DockerSandboxCodeRunner,
    get_code_runner,
)

REQUEST = CodeRunRequest(
    source_code="def add(a, b):\n    return a + b\n", tests_source="def test_add():\n    assert True\n"
)


class _Completed:
    """Minimal stand-in for subprocess.CompletedProcess."""

    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


@pytest.fixture
def runner(monkeypatch):
    """A runner whose Docker CLI lookup always succeeds."""
    monkeypatch.setattr(code_runner.shutil, "which", lambda _name: "/usr/bin/docker")
    return DockerSandboxCodeRunner(image="sandbox:test", docker_bin="/usr/bin/docker")


def test_score_gives_full_marks_when_tests_pass_silently():
    assert DockerSandboxCodeRunner._score("", "", 0) == (1, 1, 100.0)


def test_score_counts_passed_and_failed_tests():
    passed, total, percent = DockerSandboxCodeRunner._score("3 passed, 1 failed in 0.21s", "", 1)
    assert (passed, total, percent) == (3, 4, 75.0)


def test_score_counts_pytest_errors_as_attempted_tests():
    passed, total, percent = DockerSandboxCodeRunner._score("2 passed, 1 error", "", 1)
    assert (passed, total, percent) == (2, 3, 66.67)


def test_score_reports_zero_when_no_test_ran():
    assert DockerSandboxCodeRunner._score("collection error", "", 2) == (0, 0, 0.0)


def test_run_rejects_non_python_language(tmp_path):
    result = DockerSandboxCodeRunner(docker_bin="/usr/bin/docker").run(
        CodeRunRequest(source_code="", tests_source="", language="javascript"), tmp_path
    )
    assert result.enabled is False
    assert result.passed is False
    assert "Only Python" in result.reason


def test_run_reports_missing_docker_cli(tmp_path):
    missing = str(tmp_path / "no-such-docker-binary")
    result = DockerSandboxCodeRunner(docker_bin=missing).run(REQUEST, tmp_path)
    assert result.enabled is False
    assert "Docker CLI was not found" in result.reason


def test_run_scores_output_and_truncates_oversized_logs(monkeypatch, runner, tmp_path):
    noisy = "x" * 20_000
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return _Completed(stdout=f"{noisy}2 passed, 1 failed", stderr="", returncode=1)

    monkeypatch.setattr(code_runner.subprocess, "run", fake_run)

    result = runner.run(REQUEST, tmp_path)

    assert result.enabled is True
    assert result.passed is False
    assert result.exit_code == 1
    assert (result.passed_tests, result.total_tests) == (2, 3)
    assert result.score_percent == 66.67
    assert len(result.stdout) == 12_000
    assert captured["kwargs"]["text"] is True
    assert captured["kwargs"]["check"] is False


def test_run_writes_learner_files_into_the_workspace(monkeypatch, runner, tmp_path):
    monkeypatch.setattr(code_runner.subprocess, "run", lambda command, **kwargs: _Completed("1 passed", "", 0))
    workspace = tmp_path / "attempt-42"

    runner.run(REQUEST, workspace)

    assert (workspace / "solution.py").read_text(encoding="utf-8") == REQUEST.source_code
    assert (workspace / "test_solution.py").read_text(encoding="utf-8") == REQUEST.tests_source


def test_run_clamps_the_timeout_to_a_safe_range(monkeypatch, runner, tmp_path):
    recorded = []

    def fake_run(command, **kwargs):
        recorded.append(kwargs["timeout"])
        return _Completed("1 passed", "", 0)

    monkeypatch.setattr(code_runner.subprocess, "run", fake_run)

    runner.run(CodeRunRequest(source_code="", tests_source="", timeout_seconds=0), tmp_path)
    runner.run(CodeRunRequest(source_code="", tests_source="", timeout_seconds=999), tmp_path)

    assert recorded == [1, 60]


def test_run_reports_timeout(monkeypatch, runner, tmp_path):
    def raise_timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(cmd=command, timeout=kwargs.get("timeout", 1))

    monkeypatch.setattr(code_runner.subprocess, "run", raise_timeout)

    result = runner.run(REQUEST, tmp_path)

    assert result.enabled is True
    assert result.passed is False
    assert "timed out" in result.reason.lower()


def test_run_reports_failure_to_start_the_sandbox(monkeypatch, runner, tmp_path):
    def raise_oserror(command, **kwargs):
        raise OSError("docker daemon is not running")

    monkeypatch.setattr(code_runner.subprocess, "run", raise_oserror)

    result = runner.run(REQUEST, tmp_path)

    assert result.enabled is True
    assert result.passed is False
    assert "Failed to start Docker sandbox" in result.reason
    assert "docker daemon" in result.stderr


def test_run_still_executes_when_posix_chmod_is_unsupported(monkeypatch, runner, tmp_path):
    monkeypatch.setattr(code_runner.subprocess, "run", lambda command, **kwargs: _Completed("1 passed", "", 0))
    original_chmod = Path.chmod

    def deny_chmod(self, mode, *args, **kwargs):
        raise OSError("chmod is not supported here")

    monkeypatch.setattr(Path, "chmod", deny_chmod)
    try:
        result = runner.run(REQUEST, tmp_path)
    finally:
        monkeypatch.setattr(Path, "chmod", original_chmod)

    assert result.enabled is True
    assert result.passed is True


def test_runner_defaults_to_disabled(monkeypatch):
    monkeypatch.delenv("LLM_CODE_RUNNER", raising=False)
    assert isinstance(get_code_runner(), code_runner.DisabledCodeRunner)


def test_runner_is_enabled_only_for_explicit_docker_setting(monkeypatch):
    monkeypatch.setenv("LLM_CODE_RUNNER", " Docker ")
    assert isinstance(get_code_runner(), DockerSandboxCodeRunner)

"""The local entrypoint must explain itself when the environment is incomplete."""

import sys
from pathlib import Path

import run


def test_missing_requirements_is_empty_when_dependencies_are_installed():
    assert run.missing_requirements() == []


def test_missing_requirements_reports_distribution_names():
    missing = run.missing_requirements({"some-distribution": ("definitely_not_installed_module",)})
    assert missing == ["some-distribution"]


def test_missing_requirements_accepts_any_known_import_alias():
    assert run.missing_requirements({"python-multipart": ("python_multipart", "multipart")}) == []


def test_missing_requirements_flags_distributions_whose_imports_all_fail():
    missing = run.missing_requirements({"python-multipart": ("nope_one", "nope_two")})
    assert missing == ["python-multipart"]


def test_environment_check_passes_in_this_environment():
    assert run.check_environment() is None


def test_environment_check_rejects_old_python(monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 10, 4))

    message = run.check_environment()

    assert message is not None
    assert "3.11" in message
    assert "3.10.4" in message


def test_environment_check_names_missing_dependencies(monkeypatch):
    monkeypatch.setitem(run.RUNTIME_IMPORTS, "some-distribution", ("definitely_not_installed_module",))

    message = run.check_environment()

    assert message is not None
    assert "some-distribution" in message
    assert "requirements.lock.txt" in message
    assert "pypi.org/simple" in message


def test_main_exits_with_a_message_when_the_environment_is_broken(monkeypatch, capsys):
    monkeypatch.setitem(run.RUNTIME_IMPORTS, "some-distribution", ("definitely_not_installed_module",))

    exit_code = run.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "some-distribution" in captured.err
    assert "Traceback" not in captured.err


def test_runtime_import_list_matches_the_lock_file():
    lock = Path(__file__).resolve().parents[1] / "requirements.lock.txt"
    locked = {
        line.split("==")[0].split("[")[0].strip().lower().replace("_", "-")
        for line in lock.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }

    for distribution in run.RUNTIME_IMPORTS:
        normalized = distribution.split("[")[0].strip().lower().replace("_", "-")
        assert normalized in locked, f"{distribution} is required at runtime but missing from requirements.lock.txt"

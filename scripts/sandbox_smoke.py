from pathlib import Path
from tempfile import TemporaryDirectory

from app.code_runner import CodeRunRequest, DockerSandboxCodeRunner


SOURCE = """def add(a, b):
    return a + b
"""

TESTS = """from solution import add

def test_add_positive():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-2, 1) == -1
"""


with TemporaryDirectory(prefix="llm-sandbox-smoke-") as tmp:
    runner = DockerSandboxCodeRunner(image="llm-learning-sandbox:py312", docker_bin="docker")
    result = runner.run(CodeRunRequest(source_code=SOURCE, tests_source=TESTS, timeout_seconds=20), Path(tmp))
    print("enabled=", result.enabled)
    print("passed=", result.passed)
    print("score=", result.score_percent)
    print("tests=", result.passed_tests, "/", result.total_tests)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    assert result.enabled is True, result.reason
    assert result.passed is True, result.stderr or result.stdout
    assert result.score_percent == 100.0
    assert result.passed_tests == 2
    assert result.total_tests == 2

"""Local entrypoint for the LLM Engineering Learning application."""

import os
import sys

MINIMUM_PYTHON = (3, 11)

# Distribution -> acceptable import names. Keep in sync with requirements.lock.txt:
# anything listed here must be installed, otherwise the server would die with a
# bare ModuleNotFoundError traceback instead of an actionable message.
RUNTIME_IMPORTS: dict[str, tuple[str, ...]] = {
    "uvicorn[standard]": ("uvicorn",),
    "fastapi": ("fastapi",),
    "jinja2": ("jinja2",),
    "mistune": ("mistune",),
    "bleach": ("bleach",),
    # python-multipart renamed its module from `multipart` to `python_multipart`.
    "python-multipart": ("python_multipart", "multipart"),
}

INSTALL_HINT = """请先安装已验证的依赖组合 / install the verified dependency set first:

    pip install -r requirements.lock.txt

如果 pip 报 "Could not find a version that satisfies the requirement ..."，
通常是镜像源缺少这些固定版本（用 pip config list 查看当前源）。改用官方源：

If pip cannot find these pinned versions, your configured index mirror is
probably missing them. Install straight from PyPI instead:

    pip install -r requirements.lock.txt --index-url https://pypi.org/simple
"""


def missing_requirements(imports: dict[str, tuple[str, ...]] | None = None) -> list[str]:
    """Return the distributions that are not importable in this environment."""
    missing: list[str] = []
    for distribution, module_names in (imports or RUNTIME_IMPORTS).items():
        for module_name in module_names:
            try:
                __import__(module_name)
            except ModuleNotFoundError:
                continue
            break
        else:
            missing.append(distribution)
    return missing


def check_environment() -> str | None:
    """Return an actionable message when the server cannot start, otherwise None."""
    if sys.version_info < MINIMUM_PYTHON:
        required = ".".join(str(part) for part in MINIMUM_PYTHON)
        current = ".".join(str(part) for part in sys.version_info[:3])
        return (
            f"无法启动：需要 Python {required} 或更高版本，当前是 {current}。\n"
            f"Cannot start: Python {required}+ is required, found {current}."
        )

    missing = missing_requirements()
    if missing:
        return "无法启动：缺少运行时依赖 / missing runtime dependencies: " + ", ".join(missing) + "\n\n" + INSTALL_HINT

    return None


def main() -> int:
    problem = check_environment()
    if problem:
        print(problem, file=sys.stderr)
        return 1

    import uvicorn

    uvicorn.run(
        "app.current:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8765")),
        reload=os.getenv("RELOAD", "0") == "1",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

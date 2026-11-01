# 变更日志 / Changelog

本项目自 **v1.0.0** 起使用语义化版本号；此前的提交历史未编号。

## [1.0.0] — 2026-11-01

首个带版本号的稳定基线。功能范围包含 18 周课程、191 题题库、计时考试与代码实训、能力画像、逐题自适应测试、多用户隔离与超管报表。

### Added / 新增

- **版本号落地**：`app.__version__` 与 `pyproject.toml` 的 `[project].version` 双处声明，由测试保证不漂移
- `/health` 返回 `{"status": "ok", "version": "1.0.0"}`，便于部署探活时确认版本
- `pyproject.toml` 工具链配置：显式锁定的 ruff 规则集、pytest 配置、覆盖率门槛
- CI 新增 3 个 job 并纳入聚合门禁：`coverage`、`lint`、`dependency audit`
- 新增测试 204 个（65 → 269），覆盖率从 82.3% 提升到 95.6%
- `CHANGELOG.md`

### Changed / 变更

- **开发依赖 `httpx` → `httpx2` 2.16.0**：消除 starlette 1.10 `TestClient` 的弃用警告，CI 日志警告归零
- **Dependabot 策略调整**：按生态分组（minor/patch 合成一个 PR）+ 冷却期（默认 7 天、major 30 天），并补上配置里声明但仓库不存在的 `dependencies` 标签。分组直接解决了此前"每个依赖一个 PR、锁文件相邻行互相冲突"的问题
- **全仓库格式化**：36 个 Python 文件按 `line-length = 120` 重排，逐文件 AST 对比确认语义等价
- **修复 60+ 处 lint 问题**：导入排序、`timezone.utc` → `UTC`、`setattr(m, "x", v)` → `m.x = v`、`range(0, n)` → `range(n)`、未使用导入等
- **覆盖率门槛 88 → 95**，且只在单一 `coverage` job 上执行（避免平台分支差异让同一阈值含义不同）
- **README 重写**：安装方式前置（Python / Docker / 开发测试三条路径 + 前置条件表）、功能按 8 类分组、补全环境变量表与质量门禁说明

### Dependencies / 依赖升级

| 包 | 之前 | 之后 |
|---|---|---|
| fastapi | 0.141.1 | 0.162.0 |
| uvicorn | 0.52.3 | 0.54.0 |
| mistune | 3.3.4 | 3.4.0 |
| pytest | 9.1.1 | 9.2.0 |
| httpx（dev） | 0.28.1 | 替换为 httpx2 2.16.0 |
| ruff（dev） | — | 0.17.3（新增） |
| pytest-cov（dev） | — | 7.1.0（新增） |

### Notes / 说明

- 代码执行仍默认关闭（`LLM_CODE_RUNNER=disabled`）；启用需构建沙箱镜像，仅适用于可信本地工作站
- 版本号不追踪历史功能层命名（V3/V4/V5），那几层是功能演进记录，不是发布版本
- 覆盖率未覆盖部分集中在 `app/auth.py`（89%）与 `app/adaptive_v5.py`（81%）的深层状态机；门槛设在 95% 用于防止继续恶化

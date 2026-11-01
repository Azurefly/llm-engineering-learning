# LLM Engineering Learning · 大模型工程系统学习

> 18 周 LLM / RAG / Agent 工程学习路线，配套一个**本地优先的多用户学习应用**：系统考试、代码实训、逐题自适应测试、能力画像、私人笔记与外部资料库。

![version](https://img.shields.io/badge/version-1.0.0-blue)
![python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)
![license](https://img.shields.io/badge/storage-SQLite-lightgrey)

**目录**：[快速开始](#快速开始) · [项目功能](#项目功能) · [环境变量](#环境变量) · [主要页面](#主要页面) · [数据与备份](#数据与备份) · [质量门禁](#质量门禁) · [文档](#文档索引) · [课程路线](#课程路线) · [English](#english)

---

## 快速开始

### 前置条件

| 运行方式 | 需要 |
|---|---|
| Python 直接运行 | **Python 3.11 或更高**（CI 覆盖 3.11 / 3.12） |
| Docker Compose | **Docker Engine / Docker Desktop** 与 **Compose v2** |
| 代码实训自动评分（可选） | **Docker CLI**（学习者代码在沙箱容器内执行） |

不需要外部数据库、不需要 API Key、不需要联网即可使用全部功能。

### 方式一：Python 直接运行（推荐本地使用）

```bash
git clone https://github.com/Azurefly/llm-engineering-learning.git
cd llm-engineering-learning

python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1

pip install -r requirements.lock.txt
python run.py
```

打开 <http://127.0.0.1:8765>。

`requirements.lock.txt` 是**已验证的固定版本组合**，用于可复现运行；需要主动测试新版本依赖时可改用 `requirements.txt` 的兼容范围。

### 方式二：Docker Compose

```bash
docker compose up -d --build
```

打开 <http://127.0.0.1:8765>。

- 数据保存在 named volume `llm-engineering-learning-data`（容器内 `/data`）
- `docker compose down` **不会**删除数据
- `docker compose down -v` **会**删除整个 volume，包括所有账号与学习记录
- 仅映射宿主机 `127.0.0.1:8765`，并保留 capabilities 全移除、`no-new-privileges`、受限 `/tmp` 与健康检查

### 首次使用

1. 打开 <http://127.0.0.1:8765>，进入 `/register` 注册
2. **第一个注册的账号自动成为 `SUPERADMIN`**，可进入 `/admin/users` 管理用户、启停注册、查看学习报表
3. 之后注册的账号为普通学习者，各自拥有物理隔离的学习数据库

### 开发与测试

```bash
pip install -r requirements-dev.lock.txt

ruff check .                  # 静态检查（规则集在 pyproject.toml 显式锁定）
ruff format --check .         # 格式检查
pytest -q --cov               # 全部测试 + 覆盖率门槛（低于 95% 直接失败）
```

当前：**269 个测试，覆盖率 95.6%**。

### 启用代码实训自动评分（可选）

代码执行默认**关闭**（`LLM_CODE_RUNNER=disabled`），此时提交代码不会被执行，只记录未评分状态。启用方式：

```bash
docker build -t llm-learning-sandbox:py312 sandbox
LLM_CODE_RUNNER=docker python run.py
```

沙箱以 `--network none`、`--read-only`、`--cap-drop ALL`、`--pids-limit`、内存/CPU 限制与只读工作区运行，仅适合**可信本地工作站**，不是公共多租户判题服务。详见 [docs/V3.md](docs/V3.md)。

---

## 项目功能

### 学习与内容
- 18 周路线（Week 0 基线测试 → Week 18），中英文双语课程正文
- 中英文切换共享同一份学习进度
- 阅读进度记录，**手工进度上限 99%**，满分只能由系统评分产生

### 考试与评分
- **191 道工程学习题**，19 周每周 9–13 题，覆盖 Easy / Medium / Hard 与知识点标签
- 随机组卷、阶段考试（5 个阶段）、错题本与错题专项复习、成绩趋势
- 倒计时、自动保存、超时自动交卷、系统评分、成绩单与重考
- 单选 / 多选 / 判断 / 填空确定性评分；简答题按 Rubric 给部分分
- **历史试卷冻结题目快照**，后续题库更新不改变旧成绩含义

### 代码实训
- 17 个 pytest 系统评分实训（Week 2–18）
- 可选 Docker Sandbox 执行；默认关闭，任意代码不会被隐式执行

### 能力画像与自适应测试
- **V4 能力画像**：从真实考试与代码实训自动计算知识点掌握度、可信度、六维雷达与薄弱点
- **V5 逐题自适应（CAT）**：每题作答后按掌握度、难度、表现与历史曝光次数选下一题
- 进行中的自适应测试可恢复 / 放弃，题目在选中时冻结快照

### 笔记、资料与检索
- Markdown 个人思考（标签 + 课程关联）
- 外部资料库：论文、教程、视频、博客、GitHub 项目
- 全局搜索：课程正文 + 当前用户笔记 + 当前用户资料（不跨用户）

### 多用户与权限
- 注册 / 登录 / 退出，每账号独立 SQLite，数据物理隔离
- 首账号自动 `SUPERADMIN`；可管理用户、重置密码、启停账号、调整角色
- **运行时开关自主注册**，立即生效无需重启；`LLM_ALLOW_REGISTRATION` 只是初始默认值
- 学习运营大屏：全员进度、Week 0–18 推进、考试/实训通过率、活跃度、单用户详情
- 管理报表只读进度类数据，**不含**笔记正文、资料正文、学习者源码与认证敏感字段

### 数据与可靠性
- SQLite + WAL + busy timeout，无需外部数据库
- **每用户独立** JSON 备份与恢复，恢复前自动安全快照，滚动自动备份
- 系统诊断页：SQLite integrity、题库质量、Code Runner 状态、备份状态

### 安全
- HttpOnly Session Cookie、密码 PBKDF2 哈希、改密/重置后立即撤销全部会话
- Trusted Host 校验、跨站写请求拦截、安全响应头、敏感页面 `no-store`
- 管理员报表与导出不泄露密码哈希、`storage_key`、笔记与源码

---

## 环境变量

全部可选，未设置时使用下列默认值。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `HOST` | `127.0.0.1` | 监听地址（Docker 内为 `0.0.0.0`） |
| `PORT` | `8765` | 监听端口 |
| `RELOAD` | `0` | `1` 时开启 uvicorn 自动重载（仅开发） |
| `LLM_LEARNING_DATA_DIR` | `./data` | 数据根目录（Docker 内为 `/data`） |
| `LLM_ALLOW_REGISTRATION` | `1` | 自主注册的**初始**默认值；后台开关一旦保存即以后台为准 |
| `LLM_SESSION_DAYS` | `30` | 会话有效期（天） |
| `LLM_COOKIE_SECURE` | `0` | `1` 时 Cookie 仅 HTTPS 传输 |
| `LLM_ALLOWED_HOSTS` | 空 | Trusted Host 白名单，逗号分隔；空则允许 `127.0.0.1`、`localhost`、`[::1]`、`testserver` |
| `LLM_AUTO_BACKUP` | `1` | 自动备份开关（`0`/`false`/`no`/`off` 关闭） |
| `LLM_AUTO_BACKUP_HOURS` | `24` | 自动备份间隔小时数（钳制 1–168） |
| `LLM_AUTO_BACKUP_KEEP` | `10` | 保留的自动备份份数（钳制 2–50） |
| `LLM_RESTORE_MAX_MB` | `50` | 单次恢复上传上限 MB（钳制 1–500） |
| `LLM_CODE_RUNNER` | `disabled` | 设为 `docker` 才启用代码沙箱执行 |
| `LLM_CODE_RUNNER_IMAGE` | `llm-learning-sandbox:py312` | 沙箱镜像名 |
| `LLM_EXAM_WEEKLY_MINUTES` | `30` | 周测时长分钟（钳制 5–180） |
| `LLM_EXAM_STAGE_MINUTES` | `50` | 阶段考试时长分钟（钳制 5–180） |
| `LLM_EXAM_MISTAKE_MINUTES` | `20` | 错题复习时长分钟（钳制 5–180） |
| `LLM_ADAPTIVE_MAX_ITEMS` | `12` | 单次自适应测试题目上限 |

模板见 [`.env.example`](.env.example)。

---

## 主要页面

| 功能 | 地址 |
|---|---|
| 学习总览 | `/` |
| 课程正文 | `/course/{lesson_key}` |
| 登录 / 注册 | `/login` · `/register` |
| 考试中心 | `/exam-lab` |
| 阶段考试 | `/stage-exams` |
| 代码实训 | `/coding-labs` |
| 错题本 | `/mistakes` |
| 成绩趋势 | `/exam-history` |
| 题库总览 | `/question-bank` |
| 自适应学习画像 | `/adaptive` |
| 逐题自适应测试 | `/adaptive-test` |
| 思考笔记 | `/thoughts` |
| 外部资料 | `/resources` |
| 全局搜索 | `/search` |
| 我的账号 | `/account` |
| 数据与备份 | `/data-management` |
| 系统诊断 | `/diagnostics` |
| 健康检查 | `/health` |
| 超级管理员：用户管理 | `/admin/users` |
| 超级管理员：学习运营大屏 | `/admin/report` |
| 超级管理员：报表 JSON | `/admin/report/data` |
| OpenAPI 文档 | `/api/docs` |

---

## 数据与备份

```text
data/
├─ accounts.db                     # 账号、Session、系统设置（注册开关等）
├─ learning.db                     # 旧单用户版本的历史数据（升级时继承）
└─ users/
   └─ <storage-key>/
      ├─ learning.db               # 该用户全部学习数据
      └─ backups/                  # 自动备份与恢复前快照
```

- 课程进度、考试、错题、代码实训、笔记、资料、能力画像、自适应测试**全部在各用户自己的目录内**
- 从旧单用户版本升级时，若 `data/learning.db` 已有数据，**第一个注册的账号会自动复制并继承**，原文件保留
- 备份为纯 JSON，可在 `/data-management` 导出与恢复

---

## 质量门禁

CI（GitHub Actions）共 9 个 job，全部纳入 `llm-learning/ci-gate` 聚合状态：

| Job | 内容 |
|---|---|
| `test` ×3 | Ubuntu 3.11、Ubuntu 3.12、Windows 3.12 全量 pytest |
| `coverage` | 覆盖率门槛 **95%**（实测 95.6%，单一口径 job，避免平台差异） |
| `lint` | `ruff check .` + `ruff format --check .` |
| `dependency audit` | `pip-audit` 审计已验证依赖集 |
| `sandbox-smoke` | 真实构建代码沙箱镜像并跑评分冒烟 |
| `app-docker-smoke` | 完整 Docker Compose 冒烟：首超管、大屏、普通用户 403、用户隔离、注册策略切换、容器重启后持久化 |
| `aggregate CI gate` | 汇总上述结果并回写 commit status |

本地复现：

```bash
ruff check . && ruff format --check . && pytest -q --cov
```

---

## 文档索引

| 文档 | 中文 | English |
|---|---|---|
| 应用使用说明 | [docs/APP.md](docs/APP.md) | [docs/APP.en.md](docs/APP.en.md) |
| 多用户与数据隔离 | [docs/MULTI_USER.md](docs/MULTI_USER.md) | [docs/MULTI_USER.en.md](docs/MULTI_USER.en.md) |
| 超级管理员与报表 | [docs/ADMIN.md](docs/ADMIN.md) | [docs/ADMIN.en.md](docs/ADMIN.en.md) |
| V3 计时考试与代码实训 | [docs/V3.md](docs/V3.md) | [docs/V3.en.md](docs/V3.en.md) |
| V4 自适应与能力画像 | [docs/V4.md](docs/V4.md) | [docs/V4.en.md](docs/V4.en.md) |
| V5 逐题自适应与长期运行 | [docs/V5.md](docs/V5.md) | [docs/V5.en.md](docs/V5.en.md) |
| 验收边界 | [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md) | — |
| 变更日志 | [CHANGELOG.md](CHANGELOG.md) | — |

---

# 课程路线

一套面向软件工程师的大模型工程系统课程。目标不是只会调用 API，而是逐步达到：**理解原理、能够实现、能够评测、能够排错、能够设计生产系统，并用系统考试证明掌握程度**。

## 中文入口

- [18 周完整学习路线](ROADMAP.md)
- [学习进度](PROGRESS.md)
- [Week 0：基础能力测试](docs/00-baseline-test.md)
- [Week 1：数学与机器学习基础](docs/week01-ml-foundations.md)
- [Week 2：神经网络与 PyTorch](docs/week02-neural-network-pytorch.md)

## 学习主线

```text
数学与机器学习基础
  ↓
神经网络 / PyTorch
  ↓
Tokenizer / Language Modeling
  ↓
Transformer / Attention
  ↓
LLM API / Prompt / Structured Output
  ↓
Embedding / Vector Search
  ↓
RAG / Advanced RAG / RAG Evaluation
  ↓
Tool Calling / Agent
  ↓
Agent Runtime / State Machine / Guardrails
  ↓
MCP
  ↓
LiteLLM / Model Router
  ↓
Evaluation / Observability / Security
  ↓
Ollama / llama.cpp / vLLM
  ↓
Fine-tuning / LoRA
  ↓
Coding Agent
```

建议周期：18 周；每周 6～10 小时；主语言 Python。完成标准不是"看完教程"，而是：**能解释 + 能实现 + 能排错 + 能设计 + 能通过系统考试与实训**。

---

# English

A systematic, engineering-oriented curriculum for LLMs, RAG, agents, evaluation and deployment — shipped with a local-first learning application.

## English Quick Start

```bash
git clone https://github.com/Azurefly/llm-engineering-learning.git
cd llm-engineering-learning

python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.lock.txt
python run.py                        # http://127.0.0.1:8765
```

Or with Docker:

```bash
docker compose up -d --build         # http://127.0.0.1:8765
```

Requirements: Python ≥ 3.11 (CI covers 3.11 / 3.12) or Docker with Compose v2. No external database, no API key, no network access required.

**The first registered account becomes `SUPERADMIN`** and can manage users and toggle public registration at runtime.

Development and verification:

```bash
pip install -r requirements-dev.lock.txt
ruff check . && ruff format --check . && pytest -q --cov   # coverage floor 95%
```

## English Features

- **Curriculum**: 18 weeks (Week 0 baseline → Week 18), bilingual content, shared progress across languages
- **Exams**: 191 tagged questions across 19 weeks, randomized and staged papers, countdown with autosave and auto-submit, system grading only — self-reported scores are impossible
- **Question types**: single/multiple choice, true-false, fill-in graded deterministically; short answers scored against a rubric for partial credit
- **Coding labs**: 17 pytest-graded labs (Week 2–18) with an optional hardened Docker sandbox, disabled by default
- **Mastery analytics (V4)**: knowledge-point mastery, confidence and six-axis radar derived only from real exam and lab evidence
- **Sequential adaptive testing (V5)**: next question chosen from mastery, difficulty, recent performance and exposure history
- **Private data**: per-user isolated SQLite, Markdown notes, external resource library, per-user search
- **Multi-user**: registration/login, superadmin governance, runtime registration switch, cross-user progress dashboards that never expose notes, resources, learner code or credential fields
- **Operations**: per-user JSON backup/restore with pre-restore snapshots, rolling auto-backup, diagnostics page, Trusted Host and cross-site write protection
- **Quality gates**: 269 tests, 95.6% coverage floor, pinned ruff rule set, dependency audit, Docker smoke tests

## English Entry Points

- [18-Week Roadmap](ROADMAP.en.md)
- [Learning Progress Tracker](PROGRESS.en.md)
- [Week 0: Baseline Assessment](docs/00-baseline-test.en.md)
- [Week 1: Math & Machine Learning Foundations](docs/week01-ml-foundations.en.md)
- [Week 2: Neural Networks & PyTorch](docs/week02-neural-network-pytorch.en.md)
- [App Guide](docs/APP.en.md) · [Multi-User](docs/MULTI_USER.en.md) · [Administration](docs/ADMIN.en.md) · [V3](docs/V3.en.md) · [V4](docs/V4.en.md) · [V5](docs/V5.en.md)

Recommended duration: 18 weeks, 6–10 hours per week, primarily using Python. Completion means being able to **explain, implement, debug, design, and pass the corresponding system-graded assessments and coding labs**.

---

# Core Resources / 核心学习资源

- [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course)
- [Dive into Deep Learning / 动手学深度学习](https://zh.d2l.ai/)
- [PyTorch Tutorials](https://docs.pytorch.org/tutorials/)
- [Hugging Face LLM Course](https://huggingface.co/learn/llm-course/en/chapter1/1)
- [Andrej Karpathy — Neural Networks: Zero to Hero](https://karpathy.ai/zero-to-hero.html)
- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [Stanford CS224N](https://web.stanford.edu/class/cs224n/)
- [OpenAI Developer Docs](https://developers.openai.com/api/docs/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Ragas](https://docs.ragas.io/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [LiteLLM](https://docs.litellm.ai/)
- [Ollama](https://docs.ollama.com/)
- [vLLM](https://docs.vllm.ai/)
- [Hugging Face PEFT](https://huggingface.co/docs/peft/)
- [OWASP GenAI Security Project](https://genai.owasp.org/)

## Mastery Levels / 掌握等级

| Level | 中文 | English |
|---|---|---|
| L0 | 未接触 | Not exposed |
| L1 | 知道是什么 | Know what it is |
| L2 | 能清楚解释 | Can explain clearly |
| L3 | 能自己编码实现 | Can implement independently |
| L4 | 能排查真实问题 | Can debug real failures |
| L5 | 能设计生产级系统 | Can design production systems |

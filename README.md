# LLM Engineering Learning / 大模型工程系统学习

[中文](#中文) · [English](#english)

> 18 周 LLM / RAG / Agent 工程学习路线 + 多用户本地学习、系统考试、代码实训、自适应测试与知识记录应用。

## Local Learning App / 本地学习应用

当前稳定入口：`app.current:app`。

核心能力：

- **多用户注册 / 登录 / 退出**；每个账号使用独立 SQLite 学习数据库，用户之间数据物理隔离。
- 第一个账号自动成为 `SUPERADMIN`；超级管理员可管理用户、重置密码、启停账号和角色。
- 超级管理员可在后台**即时开启/停止自主注册**，无需重启；`LLM_ALLOW_REGISTRATION` 只作为未保存后台策略时的初始默认值。
- 超级管理员拥有**学习运营大屏**：查看全员学习进度、Week 0～18 推进、考试/代码实训通过率、活跃度与单用户进度详情。
- 管理报表只读取进度、考试、代码实训统计；不会展示个人思考笔记、外链正文、学习者代码源文件或认证敏感字段。
- 中英文课程切换，同一用户的学习进度跨语言共享。
- 阅读进度记录；手工进度最高 99%，**考试成绩禁止手工录入**。
- 系统考试：随机组卷、Easy / Medium / Hard、知识点标签、倒计时、自动保存、超时交卷、系统评分、成绩单与重考。
- 单选、多选、判断、填空确定性评分；简答题按照 Rubric 自动给部分分。
- 错题本、错题专项复习、阶段考试、成绩趋势。
- Python 代码实训：可选 Docker Sandbox + pytest 自动评分；任意代码执行默认安全关闭。
- V4 能力画像：从真实考试与代码实训自动计算知识点掌握度、可信度、六维能力雷达和薄弱知识点。
- **V5 逐题自适应测试（CAT）**：每答一题再根据当前掌握度、难度、刚才的表现和历史曝光次数选择下一题。
- 进行中的自适应测试可恢复/放弃，题目在选中时即冻结快照。
- 约 **190+ 工程学习题**；Week 0～18 均包含基础、理解、工程场景/排障和设计类问题，并有 CI 题库质量门禁。
- Week 2～18 每周至少一个 pytest 系统评分代码实训。
- 历史试卷完整冻结题目快照，未来更新题库不会改变旧成绩单含义。
- Markdown 个人思考、标签和课程关联。
- 外部学习链接库：论文、教程、视频、博客、GitHub 项目等。
- 全局搜索：课程 Markdown + 当前用户个人思考 + 当前用户外部链接。
- SQLite 本地持久化，WAL + busy timeout，无需额外数据库。
- **每个用户独立** JSON 备份、恢复前安全快照与滚动自动备份。
- 系统诊断页：SQLite integrity、题库质量、Code Runner、备份状态。
- Trusted Host、跨站写请求防护、安全响应头、HttpOnly Session Cookie。
- Python 直接启动和加固后的 Docker Compose 启动。
- GitHub Actions 验证：跨平台 pytest、注册/隔离/管理员报表测试、代码沙箱 Smoke Test、Docker 登录/持久化/权限/注册策略 Smoke Test。

### 注册、超级管理员与数据隔离

默认的首次注册策略来自：

```text
LLM_ALLOW_REGISTRATION=1
```

第一个成功注册的账号自动成为 `SUPERADMIN`。登录后可进入“用户管理”直接点击：

```text
停止自主注册
开启自主注册
```

后台设置保存在 `accounts.db`，修改后立即生效；不需要重启 Python 或 Docker。关闭自主注册后，`/register` 返回 `403`，已有账号仍可登录，超级管理员仍可手工创建用户。

数据结构：

```text
data/
├─ accounts.db
└─ users/
   ├─ <storage-key-A>/learning.db
   └─ <storage-key-B>/learning.db
```

`accounts.db` 保存账号、Session 与系统注册策略；课程进度、考试、错题、代码实训、思考、外链、能力画像、自适应测试和备份全部位于各用户自己的目录中。

超级管理员的大屏会跨用户只读汇总：

```text
lesson_progress
exam_attempts
code_attempts
```

不会把 `thoughts`、外链正文、`source_code`、`password_hash`、`storage_key` 等敏感内容放进管理员报表。

从旧单用户版本升级时，如果 `data/learning.db` 已经存在学习数据，**第一个成功注册的账号会自动复制并继承这些历史数据**，原文件不会自动删除。

详细说明：

- [多用户、注册与数据隔离（中文）](docs/MULTI_USER.md)
- [Multi-User Registration & Data Isolation](docs/MULTI_USER.en.md)
- [超级管理员、用户管理与学习报表](docs/ADMIN.md)
- [Superadmin, User Administration & Learning Reports](docs/ADMIN.en.md)

### Python

推荐使用已验证依赖组合：

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.lock.txt
python run.py
```

打开：`http://127.0.0.1:8765`

Python 模式中：

```text
data/accounts.db
# 账号 / Session / 系统设置

data/users/<storage-key>/learning.db
# 各用户独立学习数据
```

开发/主动测试新版依赖时，也可以使用 `requirements.txt` 的兼容范围。

### Docker Compose

```bash
docker compose up -d --build
```

打开：`http://127.0.0.1:8765`

Docker 默认使用 named volume `llm-engineering-learning-data` 保存整个 `/data`：账号库位于 `/data/accounts.db`，各用户学习数据位于 `/data/users/<storage-key>/learning.db`。`docker compose down` 不会删除数据；只有显式执行 `docker compose down -v` 才会删除整个 volume，包括**所有用户账号与学习记录**。

Compose 只映射宿主机 `127.0.0.1:8765`，并保留 Linux capabilities 全移除、`no-new-privileges`、受限 `/tmp` 与应用健康检查。

### 主要页面

| 功能 | 地址 |
|---|---|
| 登录 | `/login` |
| 注册 | `/register` |
| 学习总览 | `/` |
| 自适应学习画像 | `/adaptive` |
| 逐题自适应测试 | `/adaptive-test` |
| 考试中心 | `/exam-lab` |
| 代码实训 | `/coding-labs` |
| 错题本 | `/mistakes` |
| 成绩趋势 | `/exam-history` |
| 思考笔记 | `/thoughts` |
| 外部资料 | `/resources` |
| 全局搜索 | `/search` |
| 我的账号 | `/account` |
| 数据与备份 | `/data-management` |
| 系统诊断 | `/diagnostics` |
| 超级管理员用户管理 | `/admin/users` |
| 超级管理员学习运营大屏 | `/admin/report` |
| 超级管理员报表 JSON | `/admin/report/data` |

详细说明：

- [中文应用文档](docs/APP.md)
- [English App Guide](docs/APP.en.md)
- [多用户、注册与数据隔离](docs/MULTI_USER.md)
- [Multi-User Registration & Data Isolation](docs/MULTI_USER.en.md)
- [超级管理员、用户管理与学习报表](docs/ADMIN.md)
- [Superadmin, User Administration & Learning Reports](docs/ADMIN.en.md)
- [V3：计时考试与代码实训](docs/V3.md)
- [V3: Timed Exams & Coding Labs](docs/V3.en.md)
- [V4：自适应学习与能力画像](docs/V4.md)
- [V4: Adaptive Learning & Mastery Profile](docs/V4.en.md)
- [V5：逐题自适应测试与长期运行](docs/V5.md)
- [V5: Sequential Adaptive Testing & Long-Term Local Operation](docs/V5.en.md)

---

# 中文

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

建议周期：18 周；每周 6～10 小时；主语言 Python。完成标准不是“看完教程”，而是：**能解释 + 能实现 + 能排错 + 能设计 + 能通过系统考试与实训**。

---

# English

A systematic engineering-oriented curriculum for LLMs, RAG, agents, evaluation, deployment, and AI coding systems.

The local-first application supports multi-user registration/login with physically isolated per-user SQLite learning databases, superadmin account governance and cross-user progress dashboards, runtime public-registration control, system-graded randomized/timed exams, coding labs, mastery analytics, sequential adaptive testing, private notes/resources, per-user backups, and deployment diagnostics. Scores and mastery cannot be self-entered.

## English Entry Points

- [18-Week Roadmap](ROADMAP.en.md)
- [Learning Progress Tracker](PROGRESS.en.md)
- [Week 0: Baseline Assessment](docs/00-baseline-test.en.md)
- [Week 1: Math & Machine Learning Foundations](docs/week01-ml-foundations.en.md)
- [Week 2: Neural Networks & PyTorch](docs/week02-neural-network-pytorch.en.md)

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

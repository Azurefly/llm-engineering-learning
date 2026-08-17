# LLM Engineering Learning / 大模型工程系统学习

[中文](#中文) · [English](#english)

> 18 周 LLM / RAG / Agent 工程学习路线 + 本地学习、系统考试、代码实训、自适应测试与知识记录应用。

## Local Learning App / 本地学习应用

当前稳定入口：`app.current:app`。

核心能力：

- 中英文课程切换，学习进度跨语言共享。
- 阅读进度记录；手工进度最高 99%，**考试成绩禁止手工录入**。
- 系统考试：随机组卷、Easy / Medium / Hard、知识点标签、倒计时、自动保存、超时交卷、系统评分、成绩单与重考。
- 单选、多选、判断、填空确定性评分；简答题按照 Rubric 自动给部分分。
- 错题本、错题专项复习、阶段考试、成绩趋势。
- Python 代码实训：可选 Docker Sandbox + pytest 自动评分；任意代码执行默认安全关闭。
- V4 能力画像：从真实考试与代码实训自动计算知识点掌握度、可信度、六维能力雷达和薄弱知识点。
- **V5 逐题自适应测试（CAT）**：每答一题再根据当前掌握度、难度、刚才的表现和历史曝光次数选择下一题。
- 进行中的自适应测试可恢复/放弃，题目在选中时即冻结快照。
- 约 **190+ 工程学习题**；Week 0～18 均包含基础、理解、工程场景/排障和设计类问题，并有 CI 题库质量门禁。
- 历史试卷完整冻结题目快照，未来更新题库不会改变旧成绩单含义。
- Markdown 个人思考、标签和课程关联。
- 外部学习链接库：论文、教程、视频、博客、GitHub 项目等。
- 全局搜索：课程 Markdown + 个人思考 + 外部链接。
- SQLite 本地持久化，WAL + busy timeout，无需额外数据库。
- 完整 JSON 备份与校验恢复，恢复前自动安全快照。
- 启动时滚动自动备份，默认 24 小时一次、保留 10 份。
- 系统诊断页：SQLite integrity、题库质量、Code Runner、备份状态。
- Trusted Host、跨站写请求防护和安全响应头。
- Python 直接启动和加固后的 Docker Compose 启动。
- GitHub Actions 三层验证：pytest、代码沙箱 Smoke Test、最终 Docker Compose Smoke Test。

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

开发/主动测试新版依赖时，也可以使用 `requirements.txt` 的兼容范围。

### Docker Compose

```bash
docker compose up -d --build
```

打开：`http://127.0.0.1:8765`

学习数据保存在 `data/learning.db`。`data/*` 默认全部排除在 Git 之外。Compose 只映射宿主机 `127.0.0.1:8765`，并启用只读根文件系统、能力移除、`no-new-privileges` 和健康检查。

### 主要页面

| 功能 | 地址 |
|---|---|
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
| 数据与备份 | `/data-management` |
| 系统诊断 | `/diagnostics` |

详细说明：

- [中文应用文档](docs/APP.md)
- [English App Guide](docs/APP.en.md)
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

The local-first application provides system-graded randomized and timed exams, coding labs, mastery analytics, sequential adaptive testing, notes/resources, global search, reproducible backups, and deployment diagnostics. Scores and mastery cannot be self-entered.

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

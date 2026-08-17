# LLM Engineering Learning / 大模型工程系统学习

[中文](#中文) · [English](#english)

> 18 周 LLM / RAG / Agent 工程学习路线 + 本地学习应用。课程、系统考试、进度、个人思考和外部资料统一放在一个 local-first 工作区中。

## Local Learning App / 本地学习应用

应用支持：

- 中英文课程切换，进度共享。
- 阅读进度记录；手工进度最高 99%。
- 独立考试中心：开始考试 → 作答 → 提交 → 系统评分 → 成绩单 → 重考。
- **禁止手工录入考试成绩**；只有考试系统可以写入课程成绩。
- 通过考试后自动将课程标为 100% / 已完成；未通过保持学习中。
- 单选、多选、判断、填空确定性自动判分；简答题按知识点 Rubric 给部分分。
- **随机组卷**：按难度平衡从题库抽题，并保存本次试卷快照。
- **题目元数据**：Easy / Medium / Hard 难度与知识点标签。
- **错题本**：只保留最新一次仍然答错的题目，可一键生成错题专项复习。
- **成绩趋势**：统计考试次数、平均分、最高分、通过率和最近成绩走势。
- **阶段考试**：按 18 周路线划分为 5 个阶段，跨 Week 综合抽题。
- **题库概览**：查看每周题量、题型、难度和知识点覆盖。
- 保存每次考试 Attempt、原始答案、逐题得分、总分、最高成绩、通过状态和试卷快照。
- 为后续代码题预留 `CodeRunner` 执行边界；默认安全关闭，不会直接执行任意学习者代码。
- Markdown 个人思考、标签、课程关联。
- 外部链接库：论文、教程、视频、博客、GitHub 项目等。
- SQLite 本地持久化，无需额外数据库。
- JSON 一键备份，包含考试历史、答题明细和随机试卷快照。
- Python 直接启动和 Docker Compose 启动。

### Python

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

打开：`http://127.0.0.1:8765`

### Docker Compose

```bash
docker compose up -d --build
```

打开：`http://127.0.0.1:8765`

学习数据保存在 `data/learning.db`。Docker Compose 默认也只映射到宿主机 `127.0.0.1`。

详细说明：

- [中文应用文档](docs/APP.md)
- [English App Guide](docs/APP.en.md)

---

# 中文

一套面向软件工程师的大模型工程系统课程。目标不是只会调用 API，而是逐步达到：**理解原理、能够实现、能够评测、能够排错、能够设计生产系统**。

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

建议周期：18 周；每周 6～10 小时；主语言 Python。完成标准不是“看完教程”，而是：**能解释 + 能实现 + 能排错 + 能设计，并通过对应系统考试**。

---

# English

A systematic engineering-oriented curriculum for LLMs, RAG, agents, evaluation, deployment, and AI coding systems.

The local app includes system-graded randomized weekly exams, mistake review, score history, stage exams, and question-bank analytics. Scores cannot be self-entered; passing an exam is what marks a lesson complete.

## English Entry Points

- [18-Week Roadmap](ROADMAP.en.md)
- [Learning Progress Tracker](PROGRESS.en.md)
- [Week 0: Baseline Assessment](docs/00-baseline-test.en.md)
- [Week 1: Math & Machine Learning Foundations](docs/week01-ml-foundations.en.md)
- [Week 2: Neural Networks & PyTorch](docs/week02-neural-network-pytorch.en.md)

Recommended duration: 18 weeks, 6–10 hours per week, primarily using Python. Completion means being able to **explain, implement, debug, design, and pass the corresponding system-graded assessment**.

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
- [Anthropic Docs](https://docs.anthropic.com/)
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

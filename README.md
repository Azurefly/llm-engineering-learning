# LLM Engineering Learning / 大模型工程系统学习

[中文](#中文) · [English](#english)

---

# 中文

一套面向软件工程师的系统化大模型工程学习仓库。

> 目标不是只会调用大模型 API，而是逐步达到：**理解原理、能够实现、能够评测、能够排错、能够设计生产系统**。

## 中文入口

- [18 周完整学习路线 / ROADMAP](ROADMAP.md)
- [学习进度 / PROGRESS](PROGRESS.md)
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

建议周期：18 周；每周 6～10 小时；主语言 Python。

学习比例建议：理论 30% + 编码 40% + 测试/评测 20% + 总结 10%。

完成标准不是“看完教程”，而是：**能解释 + 能实现 + 能排错 + 能设计**。

---

# English

A systematic, engineering-oriented learning repository for Large Language Models, RAG, Agents, evaluation, deployment, and AI coding systems.

> The goal is not merely to call an LLM API. The target is to progressively reach the ability to **understand the underlying principles, implement systems from scratch, evaluate them, debug failures, and design production-grade architectures**.

## English Entry Points

- [18-Week Roadmap](ROADMAP.en.md)
- [Learning Progress Tracker](PROGRESS.en.md)
- [Week 0: Baseline Assessment](docs/00-baseline-test.en.md)
- [Week 1: Math & Machine Learning Foundations](docs/week01-ml-foundations.en.md)
- [Week 2: Neural Networks & PyTorch](docs/week02-neural-network-pytorch.en.md)

## Learning Path

```text
Math & ML Foundations
  ↓
Neural Networks / PyTorch
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

Recommended duration: 18 weeks, 6–10 hours per week, primarily using Python.

Suggested learning mix: 30% theory + 40% implementation + 20% testing/evaluation + 10% review.

Completion is not defined by “finishing the tutorial.” It means being able to **explain, implement, debug, and design**.

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

---

# Mastery Levels / 掌握等级

| Level | 中文 | English |
|---|---|---|
| L0 | 未接触 | Not exposed |
| L1 | 知道是什么 | Know what it is |
| L2 | 能清楚解释 | Can explain clearly |
| L3 | 能自己编码实现 | Can implement independently |
| L4 | 能排查真实问题 | Can debug real failures |
| L5 | 能设计生产级系统 | Can design production systems |

## Final Goal / 最终目标

The graduation project is a small but complete Coding Agent covering repository search, file editing, command execution, testing, state management, loop control, evaluation, permissions, and model routing.

毕业项目要求实现一个小型但完整的 Coding Agent，覆盖代码搜索、文件修改、命令执行、测试、状态管理、循环控制、评测、权限治理和模型路由。

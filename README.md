# LLM Engineering Learning

一套面向软件工程师的系统化大模型工程学习仓库。

> 目标不是“会调用大模型 API”，而是逐步达到：**理解原理、能够实现、能够评测、能够排错、能够设计生产系统**。

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

## 建议周期

- 总周期：18 周
- 每周投入：6～10 小时
- 主语言：Python
- 学习比例：理论 30% + 编码 40% + 测试/评测 20% + 总结 10%

## 使用方式

1. 先完成 [`docs/00-baseline-test.md`](docs/00-baseline-test.md) 的基线测试。
2. 在 [`PROGRESS.md`](PROGRESS.md) 记录当前得分和学习进度。
3. 按 [`ROADMAP.md`](ROADMAP.md) 的顺序推进。
4. 每周必须完成：理论学习、最小实现、异常测试、周测、工程验收。
5. 不以“看完教程”为完成标准，以“能独立解释 + 能实现 + 能排错”为标准。

## 课程目录

| 周次 | 主题 | 核心产出 |
|---|---|---|
| Week 0 | 基线测试 | 能力雷达与薄弱项 |
| Week 1 | 数学与机器学习基础 | ML Foundations Lab |
| Week 2 | 神经网络与 PyTorch | Mini MLP |
| Week 3 | Tokenizer 与语言模型 | Tokenizer Lab |
| Week 4 | Transformer | Mini Transformer |
| Week 5 | LLM API 与 Prompt | Unified LLM Client |
| Week 6 | Structured Output / Tool Calling | Tool Calling Demo |
| Week 7 | Embedding / Vector DB | Semantic Search |
| Week 8 | 基础 RAG | Mini RAG |
| Week 9 | 高级 RAG | Hybrid + Rerank RAG |
| Week 10 | RAG Evaluation | RAG Benchmark |
| Week 11 | Agent 基础 | Mini Agent |
| Week 12 | Agent 工程控制 | Agent Runtime |
| Week 13 | MCP | MCP Server |
| Week 14 | LiteLLM / Model Router | LLM Gateway |
| Week 15 | Evaluation / Observability / Security | Eval Suite |
| Week 16 | 本地模型与推理部署 | Local LLM Lab |
| Week 17 | Fine-tuning / LoRA | LoRA Lab |
| Week 18 | Coding Agent | 毕业项目 |

## 掌握等级

| Level | 标准 |
|---|---|
| L0 | 未接触 |
| L1 | 知道是什么 |
| L2 | 能清楚解释 |
| L3 | 能自己编码实现 |
| L4 | 能排查真实问题 |
| L5 | 能设计生产级系统 |

核心模块目标：

- Transformer ≥ L3
- Prompt / Structured Output ≥ L4
- Embedding / RAG ≥ L4
- Tool Calling / Agent ≥ L4
- MCP ≥ L3
- Evaluation ≥ L4
- Model Router ≥ L4
- Deployment ≥ L3
- Fine-tuning ≥ L2/L3
- Coding Agent ≥ L4

## 主要学习资料

优先使用官方文档、原论文和高质量课程：

- [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course)
- [动手学深度学习 D2L 中文版](https://zh.d2l.ai/)
- [PyTorch Tutorials](https://docs.pytorch.org/tutorials/)
- [Hugging Face LLM Course](https://huggingface.co/learn/llm-course/en/chapter1/1)
- [Andrej Karpathy - Neural Networks: Zero to Hero](https://karpathy.ai/zero-to-hero.html)
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

## 学习纪律

每个知识点都问自己四个问题：

1. 它是什么？
2. 它为什么存在？
3. 不使用它会怎样？
4. 我能否自己实现一个最小版本？

如果第 4 个问题无法完成，说明大概率仍停留在“知道”而不是“掌握”。

## 最终毕业标准

毕业项目需要实现一个最小但完整的 Coding Agent，至少包含：代码搜索、文件读取/修改、命令执行、测试、状态管理、循环限制、评测、权限控制和模型路由。

最终应能够回答三个问题：

- 模型为什么这样回答？
- 模型/Agent 出错后系统如何发现？
- 系统如何限制错误、恢复并继续完成任务？

# 大模型工程师 18 周系统学习路线

> 目标：从“会调用模型”走到“能独立设计、实现、评测、部署并治理大模型系统”。

## 总体原则

- 理论只学工程必需部分，不走纯算法研究路线。
- 每一周都必须有“理论 + 实验 + Debug + 测试 + 验收”。
- 先自己实现最小版本，再学习 LangGraph/LangChain 等框架。
- 任何“学会”都必须至少达到：能解释、能实现、能排错三个标准。
- 生产工程重点关注：可观测、评测、权限、预算、重试、恢复、回归测试。

---

# 学习阶段划分

## Phase 0 — 基线评估

- Week 0：100 分基线测试

## Phase 1 — 原理基础

- Week 1：数学与机器学习基础
- Week 2：神经网络与 PyTorch
- Week 3：Tokenizer 与语言模型
- Week 4：Transformer / Attention

## Phase 2 — LLM 应用开发

- Week 5：LLM API 与 Prompt Engineering
- Week 6：Structured Output 与 Tool Calling
- Week 7：Embedding 与 Vector DB
- Week 8：基础 RAG

## Phase 3 — 检索与 Agent

- Week 9：高级 RAG
- Week 10：RAG Evaluation
- Week 11：Agent 基础
- Week 12：Agent Runtime / Guardrails / State Machine

## Phase 4 — 工程平台能力

- Week 13：MCP
- Week 14：LiteLLM / Model Router
- Week 15：Evaluation / Observability / Security
- Week 16：本地模型与推理部署

## Phase 5 — 高级与综合

- Week 17：Fine-tuning / LoRA
- Week 18：Coding Agent 毕业项目

---

# Week 1 — 数学与机器学习基础

## 目标

能够看懂后续神经网络、Embedding、Attention 中真正会用到的数学概念，而不是重新学习完整高数课程。

## 必学

- 标量、向量、矩阵、Tensor
- Shape、Transpose、Matrix Multiplication
- Dot Product、Norm、Cosine Similarity
- 函数、导数、偏导、Chain Rule
- Gradient、Gradient Descent
- Probability、Distribution
- Log、Exp、Softmax、Cross Entropy
- Training / Validation / Test
- Regression / Classification
- Overfitting / Underfitting / Generalization
- Learning Rate / Epoch / Batch Size

## 学习资源

- [动手学深度学习 D2L](https://zh.d2l.ai/)
- [Google ML Crash Course](https://developers.google.com/machine-learning/crash-course)
- [3Blue1Brown](https://www.3blue1brown.com/)

## 实验

- 手写 Cosine Similarity。
- 手写最简单的 Gradient Descent。
- 用 NumPy 实现线性回归。
- 故意把 learning rate 调得极大、极小，观察训练行为。

## 验收

- [ ] 能解释 Gradient 为什么能指导参数更新。
- [ ] 能手算简单 Dot Product。
- [ ] 能解释 Cosine Similarity 为什么适合语义向量。
- [ ] 能解释 Overfitting。
- [ ] 实验代码全部可运行。

---

# Week 2 — 神经网络与 PyTorch

## 必学

- Neuron、Weight、Bias
- Linear Layer、Hidden Layer
- ReLU、Sigmoid、Softmax
- Forward / Backward
- Loss Function
- Autograd
- Tensor / dtype / device
- `nn.Module`
- Optimizer
- `state_dict`

## 学习资源

- [PyTorch Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)
- [Karpathy: Neural Networks Zero to Hero](https://karpathy.ai/zero-to-hero.html)

## 实验

实现一个 Mini MLP：

```text
week02_nn/
├── dataset.py
├── model.py
├── train.py
├── evaluate.py
└── README.md
```

要求：

- 自定义 Dataset。
- 划分 train/validation。
- 训练并记录 Loss。
- 保存模型。
- 重新加载模型进行推理。
- 故意制造 shape mismatch、dtype mismatch、学习率异常并定位问题。

## 验收

- [ ] 能解释 `backward()` 做了什么。
- [ ] 能解释为什么每轮通常要 `zero_grad()`。
- [ ] 能独立写出训练循环。

---

# Week 3 — Tokenizer 与语言模型

## 必学

- Character / Word / Subword Tokenization
- BPE 基本思想
- Vocabulary
- Token ID
- BOS / EOS / PAD / UNK
- Context Window
- Next Token Prediction
- Logits / Softmax / Sampling
- Greedy / Temperature / Top-K / Top-P

## 学习资源

- [Hugging Face LLM Course](https://huggingface.co/learn/llm-course/en/chapter1/1)
- [Hugging Face Tokenizers](https://huggingface.co/learn/llm-course/en/chapter2/4)

## 实验

建立 `tokenizer_lab.py`：

- 输出中文文本 token 数量。
- 输出英文文本 token 数量。
- 输出 Java / Python / JSON token 数量。
- 比较不同 tokenizer 的差异。
- 对同一个 Prompt 测试多个 temperature。

## 验收

- [ ] 能解释为什么字符数不等于 Token 数。
- [ ] 能解释 Context Window 的工程影响。
- [ ] 能解释 Temperature 与 Top-P 的区别。

---

# Week 4 — Transformer

## 核心

这是整个基础阶段最重要的一周。

## 必学

- Embedding Layer
- Positional Encoding / Position Embedding
- Self-Attention
- Query / Key / Value
- Scaled Dot Product Attention
- Causal Mask
- Multi-Head Attention
- Feed Forward Network
- Residual Connection
- LayerNorm
- Encoder / Decoder / Decoder-only

核心公式：

```text
Attention(Q,K,V) = softmax(QKᵀ / √d) V
```

必须能回答：

- Q/K/V 为什么是三个投影？
- `QKᵀ` 表示什么？
- 为什么要除 `√d`？
- Softmax 的作用是什么？
- 为什么最后乘 V？
- Causal Mask 为什么能阻止“看到未来”？

## 学习资源

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)
- [D2L Attention](https://zh.d2l.ai/chapter_attention-mechanisms/index.html)
- [D2L Transformer](https://zh.d2l.ai/chapter_attention-mechanisms/transformer.html)
- [Stanford CS224N](https://web.stanford.edu/class/cs224n/)
- [Karpathy Zero to Hero](https://karpathy.ai/zero-to-hero.html)

## 大实验

实现 `mini_transformer/`：

- Token Embedding
- Position Embedding
- Q/K/V Projection
- Causal Attention
- Multi-Head Attention
- FFN
- Residual
- LayerNorm
- Transformer Block
- LM Head
- Generate

不要求效果好，要求能追踪每个 Tensor 的 shape。

---

# Week 5 — LLM API 与 Prompt Engineering

## 必学

- OpenAI-compatible API
- Base URL / API Key / Model
- messages
- system / user / assistant
- Streaming
- Timeout
- Retry / Backoff
- Rate Limit
- Token Usage
- Latency
- Prompt Injection 基础意识

Prompt 统一结构：

```text
ROLE
GOAL
CONTEXT
RULES
WORKFLOW
OUTPUT FORMAT
```

## 资源

- [OpenAI API Docs](https://developers.openai.com/api/docs/)
- [OpenAI Prompt Engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
- [Anthropic Prompt Engineering](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)

## 工程实验

实现统一 `LLMClient`：

```python
client.chat(...)
client.stream(...)
```

要求具备：

- Provider 配置
- Timeout
- Retry
- 日志
- Usage
- Latency
- Error mapping

---

# Week 6 — Structured Output / Tool Calling

## Structured Output

学习：

- JSON Schema
- Pydantic
- Validation
- Enum / Optional
- Parse Error
- Retry Strategy

资源：

- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

## Tool Calling

理解完整链路：

```text
User
 ↓
LLM 生成 Tool Call
 ↓
Application 执行函数
 ↓
Tool Result
 ↓
LLM
 ↓
Answer
```

资源：

- [OpenAI Function Calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Ollama Tool Calling](https://docs.ollama.com/capabilities/tool-calling)

## 实验

实现：

- calculator
- read_file
- search_file
- query_database（只读模拟）

要求包含：参数校验、未知 Tool、Tool Timeout、Tool Exception。

---

# Week 7 — Embedding / Vector DB

## 必学

- Dense Vector
- Dimension
- Normalization
- Cosine / Dot Product / Euclidean
- Top-K
- ANN 基本思想
- Index
- Metadata Filter

## 资源

- [OpenAI Embeddings](https://developers.openai.com/api/docs/guides/embeddings)
- [Ollama Embeddings](https://docs.ollama.com/capabilities/embeddings)
- [FAISS](https://faiss.ai/)
- [Qdrant Quickstart](https://qdrant.tech/documentation/quickstart/)

## 实验

实现 Semantic Search：

- 准备 50～100 条小文本。
- 生成 embedding。
- 实现 Top-K。
- 比较 cosine 与 dot product。
- 使用 FAISS 或 Qdrant 重做一遍。

---

# Week 8 — 基础 RAG

## Pipeline

```text
Document
 ↓
Loader
 ↓
Chunk
 ↓
Embedding
 ↓
Vector DB
 ↓
Retriever
 ↓
Top-K
 ↓
Context Builder
 ↓
LLM
 ↓
Answer + Citation
```

## 必学

- Loader
- Chunk Size / Overlap
- Retriever
- Context Construction
- Citation
- No-answer behavior

## 实验

实现 `mini_rag/`，支持：

- Markdown
- TXT
- PDF
- Python / Java 源码
- Source citation

每个返回 Chunk 至少记录：

- source
- chunk_id
- score
- content

---

# Week 9 — 高级 RAG

## 必学

- BM25
- Hybrid Search
- Reranker
- Query Rewrite
- Multi Query
- Metadata Filter
- Parent Document Retrieval
- Context Compression
- Semantic Chunking

## 资源

- [Qdrant Hybrid Search](https://qdrant.tech/documentation/concepts/hybrid-queries/)

## 实验

比较四种方案：

1. Vector only
2. BM25 only
3. Hybrid
4. Hybrid + Reranker

准备至少 30 个查询并记录 Recall 与最终回答质量。

---

# Week 10 — RAG Evaluation

## 核心思想

禁止“感觉回答不错”。必须建立 Dataset 和指标。

## 必学

- Retrieval Recall
- Precision
- Context Precision
- Context Recall
- Answer Relevance
- Faithfulness
- Hallucination Rate

## 资源

- [Ragas](https://docs.ragas.io/)
- [DeepEval](https://deepeval.com/docs/getting-started)

## 实验

创建 `datasets/rag_eval.json`，至少 100 条：

```json
{
  "question": "...",
  "expected_answer": "...",
  "expected_sources": ["..."],
  "category": "...",
  "difficulty": "medium"
}
```

实现一键 benchmark。

---

# Week 11 — Agent 基础

## 必学

- Agent vs Workflow
- Tool
- Action
- Observation
- State
- Step
- ReAct
- Plan-and-Execute
- Reflection（理解边界，不迷信）

## 资源

- [OpenAI Agents Guide](https://developers.openai.com/api/docs/guides/agents)
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)

## 原则

这一周先不用 Agent 框架，自己实现最小循环。

## Mini Agent

Tools：

- list_files
- read_file
- write_file
- search_file
- run_python
- run_command

需要保存每一步 Tool Call / Result。

---

# Week 12 — Agent Runtime / Guardrails

## 这是工程落地重点

Agent 真正困难的是失控、循环、重复、错误工具、成本和状态污染。

## 必学

- Max Steps
- Timeout
- Token Budget
- Cost Budget
- Retry Limit
- Duplicate Action Detection
- No Progress Detection
- Circuit Breaker
- Human Approval
- State Machine
- Rollback

推荐状态：

```text
RECEIVED
ANALYZING
PLANNING
EXECUTING
VALIDATING
TESTING
REVIEWING
COMPLETED

FAILED
RETRYING
WAITING_APPROVAL
ROLLBACK
```

## 实验

主动构造：

- 重复读文件循环
- 同一个命令连续执行
- Tool 一直失败
- 模型一直修改后又改回
- Token 超预算
- Shell 危险命令

要求 Runtime 能明确终止并给出 reason。

---

# Week 13 — MCP

## 必学

- MCP Client
- MCP Server
- Tool
- Resource
- Prompt
- Transport
- JSON-RPC
- Authentication / Authorization 基础

## 资源

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP Specification](https://modelcontextprotocol.io/specification/)

## 必答问题

- MCP 与 REST API 有什么区别？
- MCP 与 Tool Calling 有什么区别？
- MCP Server 放在哪一层？
- 为什么不能因为 Tool 通过 MCP 暴露就默认可信？

## 实验

开发 `project-mcp-server`：

- read_file
- search_code
- project_info
- run_test

---

# Week 14 — LiteLLM / Model Router

## 架构

```text
Application
 ↓
Model Router
 ↓
LLM Gateway
 ↓
Providers / Local Models
```

## 资源

- [LiteLLM Docs](https://docs.litellm.ai/)
- [LiteLLM Routing](https://docs.litellm.ai/docs/routing)

## 逻辑模型

业务层不绑定 provider/model-version，而使用：

- fast
- reasoning
- coding
- long-context
- cheap
- local

## Router 输入建议

```json
{
  "task_type": "coding",
  "difficulty": "hard",
  "context_tokens": 32000,
  "need_tools": true,
  "privacy": "internal",
  "priority": "quality"
}
```

## 实验

实现：

- Rule Router
- Cost Router
- Capability Router
- Fallback
- Retry
- Cooldown
- Latency / Cost logging

---

# Week 15 — Evaluation / Observability / Security

## Evaluation

必须覆盖：

- Accuracy
- Relevance
- Faithfulness
- Format Accuracy
- Tool Selection Accuracy
- Tool Argument Accuracy
- Goal Success Rate
- Average Steps
- Retry Rate
- Loop Rate
- Latency
- Cost

## Observability

Trace 至少记录：

```text
request_id
model
prompt_tokens
output_tokens
latency
step
state
tool
tool_args
tool_result
error
cost
final_status
```

## Security

重点：

- Prompt Injection
- Indirect Prompt Injection
- Tool Injection
- Excessive Agency
- Sensitive Information Disclosure
- Permission Boundary
- Human Approval

## 资源

- [OWASP GenAI Security](https://genai.owasp.org/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

---

# Week 16 — 本地模型与推理部署

## Ollama

- Model management
- API
- Embedding
- Tool Calling
- Structured Output
- OpenAI compatibility

资源：

- [Ollama Docs](https://docs.ollama.com/)

## llama.cpp

学习：

- GGUF
- CPU inference
- GPU offload
- Quantization

资源：

- [llama.cpp](https://github.com/ggml-org/llama.cpp)

## vLLM

学习：

- Serving
- OpenAI-compatible Server
- Batching
- KV Cache
- Concurrency

资源：

- [vLLM Docs](https://docs.vllm.ai/)

## 指标

- TTFT
- Tokens/s
- Total Latency
- Throughput
- VRAM
- Concurrency

---

# Week 17 — Fine-tuning / LoRA

## 学习顺序

先明确三种方法的边界：

```text
Prompt → 调整任务表达与行为约束
RAG → 补充外部/动态知识
Fine-tuning → 调整稳定行为模式、风格或专项能力
```

## 必学

- Pretraining
- SFT
- PEFT
- LoRA
- QLoRA
- Dataset quality
- Train / Eval split
- Overfitting
- DPO 基本思想

## 资源

- [Hugging Face PEFT](https://huggingface.co/docs/peft/)
- [LoRA Guide](https://huggingface.co/docs/peft/main/conceptual_guides/lora)
- [TRL SFTTrainer](https://huggingface.co/docs/trl/sft_trainer)

## 实验

准备 500～2000 条小型训练集，比较：

- Base model
- Better Prompt
- RAG
- LoRA tuned model

必须写结论：微调到底改善了什么，什么没有改善。

---

# Week 18 — Coding Agent 毕业项目

## 目标

实现一个真实可运行的最小 Coding Agent，而不是 Chat UI Demo。

## 架构

```text
User Task
  ↓
Understand
  ↓
Repository Context
  ↓
Plan
  ↓
Execute Tools
  ↓
Validate
  ↓
Compile/Test
  ↓
Analyze Failure
  ↓
Repair
  ↓
Review Diff
  ↓
Complete
```

## Tools

至少实现：

- list_files
- read_file
- search_text
- search_symbol
- write_file / patch_file
- run_command
- run_test
- git_diff

## Runtime 必须包含

- Max Steps
- Timeout
- Token / Cost Budget
- Duplicate Action Detection
- Progress Check
- Approval policy
- Trace
- Error recovery

## Repository Context

学习：

- [Aider Repository Map](https://aider.chat/docs/repomap.html)
- [Continue Documentation](https://docs.continue.dev/)

思考：大型代码库不可能把所有源码塞入 Context，应如何用搜索、symbol、repository map、RAG 和动态上下文组合解决？

## 最终验收任务

随机选择一个真实 Python 项目，给 Agent：

1. 新增一个小功能；
2. 修复一个人为制造的 bug；
3. 修改后运行测试；
4. 测试失败必须自动分析；
5. 最终生成 diff summary；
6. 不允许未经批准执行危险操作。

---

# 每周统一考试模板

总分 100：

| 模块 | 分数 |
|---|---:|
| 基础概念 | 20 |
| 原理理解 | 20 |
| 编程实现 | 30 |
| Debug | 15 |
| Architecture | 15 |

- 80：通过
- 90：优秀
- <70：建议先补课，不直接推进核心新内容

---

# 四次阶段考试

## Exam 1 — Week 4

范围：ML / NN / Tokenizer / Transformer。

## Exam 2 — Week 8

范围：LLM API / Prompt / Structured Output / Tool Calling / Embedding / RAG。

## Exam 3 — Week 12

范围：Advanced RAG / Evaluation / Agent / Runtime。

## Exam 4 — Week 16

范围：MCP / Router / LiteLLM / Eval / Security / Deployment。

## Final — Week 18

完整 Coding Agent 工程验收。

---

# 最终能力验收问题

完成后，应能不依赖 AI 清楚回答：

- [ ] LLM 为什么能生成文字？
- [ ] Token 与字符有什么差异？
- [ ] Embedding 为什么可以用于语义检索？
- [ ] Attention 计算了什么？
- [ ] Q/K/V 是什么？
- [ ] 为什么需要 Causal Mask？
- [ ] 为什么模型会幻觉？
- [ ] RAG 为什么只能降低而不能消除幻觉？
- [ ] Chunk Size 如何选择？
- [ ] Reranker 为什么有效？
- [ ] Tool Calling 的执行者是谁？
- [ ] Agent 和 Workflow 如何选择？
- [ ] Agent 为什么死循环？
- [ ] 如何从工程上检测“无进展”？
- [ ] MCP 解决什么问题？
- [ ] LiteLLM 解决什么问题？
- [ ] Model Router 应考虑哪些信号？
- [ ] Prompt / RAG / Fine-tuning 各解决什么问题？
- [ ] 如何做 LLM Regression Test？
- [ ] 如何评测 RAG？
- [ ] 如何评测 Agent？
- [ ] Prompt Injection 如何进入 Tool 链路？
- [ ] 什么 Tool 必须 Human Approval？
- [ ] TTFT、TPS、Throughput 有什么区别？
- [ ] KV Cache 为什么占显存？
- [ ] LoRA 为什么比全参数微调轻量？
- [ ] Coding Agent 如何理解大型 Repository？

如果这些问题中 90% 能清楚解释，并能独立完成毕业项目，说明已经形成较完整的大模型工程知识体系。

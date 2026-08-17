# 18-Week LLM Engineering Roadmap

> Goal: progress from “I can call an LLM” to “I can independently design, implement, evaluate, deploy, debug, and govern production-grade LLM systems.”

## Core Principles

- Learn only the math and theory that materially improves engineering judgment.
- Every week must include theory, implementation, debugging, testing, and acceptance criteria.
- Implement a minimal version before relying on orchestration frameworks.
- “Learned” means at least: explain it, implement it, and debug it.
- Production engineering must include observability, evaluation, permission boundaries, budgets, retries, recovery, and regression testing.

---

# Phase Structure

## Phase 0 — Baseline

- Week 0: 100-point baseline assessment

## Phase 1 — Foundations

- Week 1: Math & Machine Learning Foundations
- Week 2: Neural Networks & PyTorch
- Week 3: Tokenizers & Language Modeling
- Week 4: Transformer & Attention

## Phase 2 — LLM Application Development

- Week 5: LLM APIs & Prompt Engineering
- Week 6: Structured Output & Tool Calling
- Week 7: Embeddings & Vector Databases
- Week 8: Basic RAG

## Phase 3 — Retrieval & Agents

- Week 9: Advanced RAG
- Week 10: RAG Evaluation
- Week 11: Agent Fundamentals
- Week 12: Agent Runtime / Guardrails / State Machines

## Phase 4 — Platform Engineering

- Week 13: MCP
- Week 14: LiteLLM / Model Routing
- Week 15: Evaluation / Observability / Security
- Week 16: Local Models & Inference Serving

## Phase 5 — Advanced Topics & Capstone

- Week 17: Fine-tuning / LoRA
- Week 18: Coding Agent Graduation Project

---

# Week 1 — Math & Machine Learning Foundations

## Goal

Understand the math actually used by neural networks, embeddings, and attention without turning the course into a full mathematics degree.

## Required Topics

- Scalars, vectors, matrices, tensors
- Shape, transpose, matrix multiplication
- Dot product, norm, cosine similarity
- Functions, derivatives, partial derivatives, chain rule
- Gradient and gradient descent
- Probability and distributions
- Log, exp, softmax, cross entropy
- Training / validation / test splits
- Regression / classification
- Overfitting / underfitting / generalization
- Learning rate / epoch / batch size

## Resources

- [Dive into Deep Learning](https://d2l.ai/)
- [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course)
- [3Blue1Brown](https://www.3blue1brown.com/)

## Lab

- Implement cosine similarity from scratch.
- Implement a basic gradient descent loop.
- Implement linear regression in NumPy.
- Deliberately test learning rates that are far too large and too small.

## Acceptance Criteria

- [ ] Explain why gradients guide parameter updates.
- [ ] Compute a simple dot product by hand.
- [ ] Explain why cosine similarity is useful for embeddings.
- [ ] Explain overfitting in engineering terms.
- [ ] All lab code runs successfully.

---

# Week 2 — Neural Networks & PyTorch

## Required Topics

- Neuron, weight, bias
- Linear layers and hidden layers
- ReLU, sigmoid, softmax
- Forward and backward passes
- Loss functions
- Autograd
- Tensor, dtype, device
- `nn.Module`
- Optimizers
- `state_dict`

## Resources

- [PyTorch Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)
- [Karpathy: Neural Networks — Zero to Hero](https://karpathy.ai/zero-to-hero.html)

## Lab

Build a Mini MLP with:

```text
week02_nn/
├── dataset.py
├── model.py
├── train.py
├── evaluate.py
└── README.md
```

Requirements:

- Custom dataset
- Train/validation split
- Loss logging
- Save and reload the model
- Run inference after reload
- Deliberately trigger shape mismatch, dtype mismatch, device mismatch, and unstable learning rate failures

## Acceptance Criteria

- [ ] Explain what `backward()` computes.
- [ ] Explain why gradients are usually zeroed each iteration.
- [ ] Write a training loop without copying a full tutorial.

---

# Week 3 — Tokenizers & Language Modeling

## Required Topics

- Character / word / subword tokenization
- BPE intuition
- Vocabulary
- Token IDs
- BOS / EOS / PAD / UNK
- Context window
- Next-token prediction
- Logits / softmax / sampling
- Greedy decoding / temperature / Top-K / Top-P

## Resources

- [Hugging Face LLM Course](https://huggingface.co/learn/llm-course/en/chapter1/1)
- [Hugging Face Tokenizers](https://huggingface.co/learn/llm-course/en/chapter2/4)

## Lab

Create `tokenizer_lab.py` and compare token counts for:

- Chinese text
- English text
- Java code
- Python code
- JSON

Then evaluate the same prompt with multiple temperature values.

## Acceptance Criteria

- [ ] Explain why character count is not token count.
- [ ] Explain how context windows affect cost and quality.
- [ ] Explain temperature vs Top-P.

---

# Week 4 — Transformer & Attention

## Core Topics

- Embedding layer
- Positional encoding / position embeddings
- Self-attention
- Query / Key / Value
- Scaled dot-product attention
- Causal masks
- Multi-head attention
- Feed-forward networks
- Residual connections
- Layer normalization
- Encoder / decoder / decoder-only architectures

Core equation:

```text
Attention(Q,K,V) = softmax(QKᵀ / √d) V
```

You must be able to explain:

- Why Q, K, and V use separate projections
- What `QKᵀ` represents
- Why scores are scaled by `√d`
- Why softmax is applied
- Why attention weights are multiplied by V
- How causal masking prevents access to future tokens

## Resources

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)
- [Dive into Deep Learning — Attention](https://d2l.ai/chapter_attention-mechanisms-and-transformers/index.html)
- [Stanford CS224N](https://web.stanford.edu/class/cs224n/)
- [Karpathy Zero to Hero](https://karpathy.ai/zero-to-hero.html)

## Major Lab

Implement a minimal Transformer containing:

- Token embeddings
- Position embeddings
- Q/K/V projections
- Causal self-attention
- Multi-head attention
- FFN
- Residual paths
- LayerNorm
- Transformer blocks
- LM head
- Text generation

Quality is not the target; being able to trace tensor shapes is.

---

# Week 5 — LLM APIs & Prompt Engineering

## Required Topics

- OpenAI-compatible APIs
- Base URL / API key / model
- Messages and roles
- Streaming
- Timeouts
- Retry / backoff
- Rate limits
- Token usage
- Latency
- Basic prompt-injection awareness

Recommended prompt structure:

```text
ROLE
GOAL
CONTEXT
RULES
WORKFLOW
OUTPUT FORMAT
```

## Resources

- [OpenAI API Docs](https://developers.openai.com/api/docs/)
- [OpenAI Prompt Engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
- [Anthropic Prompt Engineering](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)

## Engineering Lab

Implement a provider-agnostic `LLMClient` with:

- `chat()`
- `stream()`
- Timeout handling
- Retry logic
- Usage logging
- Latency logging
- Error normalization

---

# Week 6 — Structured Output & Tool Calling

## Structured Output

Learn:

- JSON Schema
- Pydantic
- Validation
- Enum / Optional values
- Parsing errors
- Retry strategies

Resource:

- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

## Tool Calling

Understand the actual execution chain:

```text
User
 ↓
LLM produces a Tool Call
 ↓
Application executes the function
 ↓
Tool Result
 ↓
LLM
 ↓
Answer
```

Resources:

- [OpenAI Function Calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Ollama Tool Calling](https://docs.ollama.com/capabilities/tool-calling)

## Lab

Implement tools for:

- calculator
- read_file
- search_file
- read-only database query simulation

Handle argument validation, unknown tools, tool timeouts, and exceptions.

---

# Week 7 — Embeddings & Vector Databases

## Required Topics

- Dense vectors
- Dimensions
- Normalization
- Cosine / dot product / Euclidean distance
- Top-K
- Approximate nearest neighbor intuition
- Indexes
- Metadata filtering

## Resources

- [OpenAI Embeddings](https://developers.openai.com/api/docs/guides/embeddings)
- [Ollama Embeddings](https://docs.ollama.com/capabilities/embeddings)
- [FAISS](https://faiss.ai/)
- [Qdrant Quickstart](https://qdrant.tech/documentation/quickstart/)

## Lab

Create a semantic search system over 50–100 short texts:

- Generate embeddings
- Implement Top-K search
- Compare cosine and dot-product ranking
- Rebuild the experiment with FAISS or Qdrant

---

# Week 8 — Basic RAG

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

## Required Topics

- Document loading
- Chunk size / overlap
- Retrieval
- Context construction
- Citations
- No-answer behavior

## Lab

Build `mini_rag/` supporting:

- Markdown
- TXT
- PDF
- Python / Java source files
- Source citations

Every retrieved chunk should include at least:

- source
- chunk_id
- score
- content

---

# Week 9 — Advanced RAG

## Required Topics

- BM25
- Hybrid search
- Reranking
- Query rewriting
- Multi-query retrieval
- Metadata filters
- Parent-document retrieval
- Context compression
- Semantic chunking

## Resource

- [Qdrant Hybrid Queries](https://qdrant.tech/documentation/concepts/hybrid-queries/)

## Lab

Compare four retrieval configurations:

1. Vector only
2. BM25 only
3. Hybrid
4. Hybrid + reranker

Use at least 30 queries and record retrieval recall and answer quality.

---

# Week 10 — RAG Evaluation

## Principle

“Feels good” is not an evaluation method. Build datasets and metrics.

## Required Metrics

- Retrieval recall
- Precision
- Context precision
- Context recall
- Answer relevance
- Faithfulness
- Hallucination rate

## Resources

- [Ragas](https://docs.ragas.io/)
- [DeepEval](https://deepeval.com/docs/getting-started)

## Lab

Create `datasets/rag_eval.json` with at least 100 cases and fields such as:

```json
{
  "question": "...",
  "expected_answer": "...",
  "expected_sources": ["..."],
  "category": "...",
  "difficulty": "medium"
}
```

Build a one-command benchmark runner.

---

# Week 11 — Agent Fundamentals

## Required Topics

- Agent vs workflow
- Tools
- Actions
- Observations
- State
- Steps
- ReAct
- Plan-and-Execute
- Reflection and its limitations

## Resources

- [OpenAI Agents Guide](https://developers.openai.com/api/docs/guides/agents)
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)

## Rule

Do not begin with an Agent framework. Build the loop yourself first.

## Mini Agent Tools

- list_files
- read_file
- write_file
- search_file
- run_python
- run_command

Persist each tool call and observation.

---

# Week 12 — Agent Runtime, Guardrails & State Machines

## Production Focus

The difficult part of Agents is usually not tool calling. It is controlling loops, repeated actions, failures, cost, state pollution, and excessive permissions.

## Required Topics

- Max steps
- Runtime timeout
- Token budget
- Cost budget
- Retry limits
- Duplicate-action detection
- No-progress detection
- Circuit breakers
- Human approval
- State machines
- Rollback

Suggested states:

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

## Lab

Deliberately create:

- File-read loops
- Repeated shell commands
- Permanently failing tools
- Edit/revert loops
- Token-budget overruns
- Dangerous shell requests

The runtime must terminate with an explicit reason.

---

# Week 13 — MCP

## Required Topics

- MCP client
- MCP server
- Tools
- Resources
- Prompts
- Transport
- JSON-RPC
- Authentication / authorization basics

## Resources

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Specification](https://modelcontextprotocol.io/specification/)

## Questions You Must Answer

- How is MCP different from REST?
- How is MCP different from tool calling?
- Where does an MCP server fit architecturally?
- Why should an MCP-exposed tool not automatically be trusted?

## Lab

Build `project-mcp-server` exposing:

- read_file
- search_code
- project_info
- run_test

---

# Week 14 — LiteLLM & Model Routing

## Architecture

```text
Application
 ↓
Model Router
 ↓
LLM Gateway
 ↓
Providers / Local Models
```

## Resources

- [LiteLLM Docs](https://docs.litellm.ai/)
- [LiteLLM Routing](https://docs.litellm.ai/docs/routing)

## Logical Model Groups

Business logic should use capability groups rather than provider-version strings:

- fast
- reasoning
- coding
- long-context
- cheap
- local

## Suggested Router Input

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

## Lab

Implement:

- Rule routing
- Cost routing
- Capability routing
- Fallbacks
- Retries
- Cooldowns
- Latency and cost logging

---

# Week 15 — Evaluation, Observability & Security

## Evaluation

Cover at least:

- Accuracy
- Relevance
- Faithfulness
- Format accuracy
- Tool-selection accuracy
- Tool-argument accuracy
- Goal success rate
- Average steps
- Retry rate
- Loop rate
- Latency
- Cost

## Observability

A trace should include at least:

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

Study and test:

- Prompt injection
- Indirect prompt injection
- Tool injection
- Excessive agency
- Sensitive-information disclosure
- Permission boundaries
- Human approval

## Resources

- [OWASP GenAI Security](https://genai.owasp.org/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

---

# Week 16 — Local Models & Inference Serving

## Ollama

Learn:

- Model management
- APIs
- Embeddings
- Tool calling
- Structured output
- OpenAI compatibility

Resource:

- [Ollama Docs](https://docs.ollama.com/)

## llama.cpp

Learn:

- GGUF
- CPU inference
- GPU offload
- Quantization

Resource:

- [llama.cpp](https://github.com/ggml-org/llama.cpp)

## vLLM

Learn:

- Serving
- OpenAI-compatible server
- Batching
- KV cache
- Concurrency

Resource:

- [vLLM Docs](https://docs.vllm.ai/)

## Metrics

- TTFT
- Tokens/s
- Total latency
- Throughput
- VRAM usage
- Concurrency

---

# Week 17 — Fine-tuning & LoRA

## First Understand the Boundaries

```text
Prompt → adjusts task expression and behavior constraints
RAG → provides external or changing knowledge
Fine-tuning → changes stable behavior patterns, style, or specialized capability
```

## Required Topics

- Pretraining
- SFT
- PEFT
- LoRA
- QLoRA
- Dataset quality
- Train/eval splits
- Overfitting
- Basic DPO intuition

## Resources

- [Hugging Face PEFT](https://huggingface.co/docs/peft/)
- [LoRA Guide](https://huggingface.co/docs/peft/main/conceptual_guides/lora)
- [TRL SFTTrainer](https://huggingface.co/docs/trl/sft_trainer)

## Lab

Prepare 500–2000 small training examples and compare:

- Base model
- Better prompting
- RAG
- LoRA-tuned model

Write down exactly what fine-tuning improved and what it did not.

---

# Week 18 — Coding Agent Graduation Project

## Goal

Build a real, runnable mini Coding Agent rather than a chat UI demo.

## Architecture

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

## Required Tools

- list_files
- read_file
- search_text
- search_symbol
- write_file / patch_file
- run_command
- run_test
- git_diff

## Runtime Requirements

- Max steps
- Timeout
- Token / cost budget
- Duplicate-action detection
- Progress checks
- Approval policy
- Tracing
- Error recovery

## Repository Context Resources

- [Aider Repository Map](https://aider.chat/docs/repomap.html)
- [Continue Documentation](https://docs.continue.dev/)

Key design question: a large repository cannot fit into a model context window. How should search, symbols, repository maps, RAG, and dynamic context selection work together?

## Graduation Acceptance Test

Select a real Python project and ask the Agent to:

1. Add a small feature.
2. Fix an intentionally introduced bug.
3. Run tests after modification.
4. Analyze test failures automatically.
5. Produce a final diff summary.
6. Never perform dangerous operations without approval.

---

# Weekly Exam Template

Total: 100 points.

| Area | Points |
|---|---:|
| Concepts | 20 |
| Principles | 20 |
| Implementation | 30 |
| Debugging | 15 |
| Architecture | 15 |

- ≥80: Pass
- ≥90: Excellent
- <70: Review weak areas before moving on to critical new topics

---

# Stage Exams

## Exam 1 — Week 4

ML / Neural Networks / Tokenizers / Transformer

## Exam 2 — Week 8

LLM APIs / Prompt / Structured Output / Tool Calling / Embeddings / RAG

## Exam 3 — Week 12

Advanced RAG / Evaluation / Agents / Runtime

## Exam 4 — Week 16

MCP / Routing / LiteLLM / Evaluation / Security / Deployment

## Final — Week 18

End-to-end Coding Agent engineering assessment.

---

# Final Capability Checklist

At the end of the roadmap, you should be able to answer without AI assistance:

- [ ] Why can an LLM generate text?
- [ ] Why is token count different from character count?
- [ ] Why can embeddings support semantic retrieval?
- [ ] What does attention compute?
- [ ] What are Q, K, and V?
- [ ] Why is a causal mask needed?
- [ ] Why do LLMs hallucinate?
- [ ] Why can RAG reduce but not eliminate hallucination?
- [ ] How should chunk size be selected?
- [ ] Why does reranking help?
- [ ] Who actually executes a tool call?
- [ ] When should you use an Agent vs a deterministic workflow?
- [ ] Why do Agents loop?
- [ ] How can “no progress” be detected programmatically?
- [ ] What problem does MCP solve?
- [ ] What problem does LiteLLM solve?
- [ ] Which signals should a Model Router use?
- [ ] When should you choose Prompting vs RAG vs Fine-tuning?
- [ ] How do you build LLM regression tests?
- [ ] How do you evaluate RAG?
- [ ] How do you evaluate Agents?
- [ ] How can prompt injection propagate into tool execution?
- [ ] Which tools require human approval?
- [ ] What are TTFT, TPS, and throughput?
- [ ] Why does KV cache consume VRAM?
- [ ] Why is LoRA lighter than full fine-tuning?
- [ ] How should a Coding Agent understand a large repository?

If you can clearly answer at least 90% of these and independently complete the capstone, you have built a solid LLM engineering foundation.

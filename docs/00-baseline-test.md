# Week 0 — 大模型工程基础能力基线测试

> 目的：在正式学习之前判断哪些内容可以快速通过，哪些是实际短板。
>
> 规则：第一次作答不要查资料、不要使用 AI。完成后再自行核对和补学。

总分：100 分。

---

# 1. 基础概念 — 20 分

每题 2 分。

评分标准：

- 0 分：不知道或答案错误。
- 1 分：知道大概意思，但不能清楚解释机制。
- 2 分：能用自己的话解释，并能举一个工程例子。

## 题目

- [ ] 1. AI、Machine Learning、Deep Learning、LLM 之间是什么关系？
- [ ] 2. Training 和 Inference 有什么区别？
- [ ] 3. 模型 Parameter 和 Hyperparameter 有什么区别？
- [ ] 4. Loss 是什么？训练为什么需要 Loss？
- [ ] 5. Gradient 是什么？Gradient Descent 做了什么？
- [ ] 6. Epoch、Batch、Batch Size 分别是什么意思？
- [ ] 7. Overfitting 是什么？如何发现？
- [ ] 8. Token 是什么？为什么一个汉字不一定对应一个 Token？
- [ ] 9. Embedding 是什么？为什么它可以用于语义搜索？
- [ ] 10. Transformer 是什么？它相较 RNN 的核心优势是什么？

得分：`__/20`

---

# 2. LLM 原理 — 20 分

每题 2 分。

- [ ] 1. 什么是 Next Token Prediction？
- [ ] 2. Logits、Probability、Softmax 之间是什么关系？
- [ ] 3. Temperature=0 与 Temperature=1 的输出行为有什么典型差异？
- [ ] 4. Top-K 与 Top-P 各自限制了什么？
- [ ] 5. Self-Attention 在解决什么问题？
- [ ] 6. Q、K、V 分别代表什么？为什么要计算 `QK^T`？
- [ ] 7. 为什么 Attention Score 要除以 `sqrt(d)`？
- [ ] 8. 为什么 Transformer 需要位置相关信息？
- [ ] 9. Causal Mask 有什么作用？
- [ ] 10. 从“概率预测”角度解释 LLM 为什么会产生幻觉。

得分：`__/20`

---

# 3. LLM 应用开发 — 20 分

任务：不用现成 Agent/RAG 框架，写一个最小 Python LLM Client。

建议目录：

```text
baseline/
└── llm_client.py
```

每项 2 分：

- [ ] 能配置 `base_url`、`api_key`、`model`。
- [ ] 能发送 system/user messages。
- [ ] 能处理普通非流式响应。
- [ ] 能处理 Streaming。
- [ ] 能配置 Timeout。
- [ ] 能针对临时错误 Retry，并设置最大次数。
- [ ] 能记录请求耗时。
- [ ] 能读取/统计 Token Usage。
- [ ] 能要求模型返回 JSON，并做解析失败处理。
- [ ] 能统一处理网络错误、认证错误、限流、模型错误。

得分：`__/20`

## 附加问答

不计分，但建议写入学习笔记：

1. Retry 为什么不能无限重试？
2. HTTP 429 和 5xx 是否应该采用完全相同的重试策略？
3. 如果 JSON 解析失败，你会重试原请求、修复 JSON，还是重新 Prompt？为什么？
4. 如何避免日志记录敏感 Prompt/API Key？

---

# 4. RAG / Agent 基础 — 20 分

每题 2 分。

- [ ] 1. RAG 的完整 Pipeline 是什么？
- [ ] 2. Chunk 为什么不能无限大？也不能无限小？
- [ ] 3. Vector Search 与 SQL `LIKE` 的本质差异是什么？
- [ ] 4. Top-K 过大和过小分别可能产生什么问题？
- [ ] 5. Reranker 为什么常常能改善检索结果？
- [ ] 6. Tool Calling 中真正执行 Tool 的是谁？模型还是应用程序？
- [ ] 7. Agent 与普通 Chat Completion 的关键区别是什么？
- [ ] 8. Agent State 应该保存什么？什么不应该无限保存？
- [ ] 9. Agent 为什么容易产生死循环？
- [ ] 10. 至少说出 5 种限制 Agent 失控的方法。

得分：`__/20`

---

# 5. 系统设计 — 20 分

题目：

> 设计一个可以读取 Git 仓库、理解代码、修改代码、执行测试并生成最终变更说明的 Coding Agent。

请画出或文字描述系统架构。

评分项，每项 2 分：

- [ ] 1. Model Layer：如何选择模型，是否支持 fallback。
- [ ] 2. Context Layer：如何选择需要给模型的代码和文档。
- [ ] 3. Repository Search：如何搜索文件、符号、引用关系。
- [ ] 4. Planning：复杂任务如何拆分步骤。
- [ ] 5. Tool Layer：至少设计 read/search/edit/test/git 等工具。
- [ ] 6. State：如何持久化任务状态和历史 Observation。
- [ ] 7. Loop Control：最大步骤、重复行为、无进展检测。
- [ ] 8. Validation：修改代码后怎样判断修改是否合理。
- [ ] 9. Test & Recovery：测试失败后如何定位、重试、回滚。
- [ ] 10. Security：Shell、敏感文件、Git Push、生产系统如何限制权限。

得分：`__/20`

---

# 6. 总分

| 模块 | 满分 | 得分 |
|---|---:|---:|
| 基础概念 | 20 |  |
| LLM 原理 | 20 |  |
| LLM 应用 | 20 |  |
| RAG / Agent | 20 |  |
| 系统设计 | 20 |  |
| **总分** | **100** |  |

等级建议：

| 分数 | 建议 |
|---:|---|
| 0～29 | 从 Week 1 完整开始，不跳课 |
| 30～49 | 基础有碎片知识，Week 1～4 仍建议完整学习 |
| 50～64 | 可快速复习 Week 1～2，但 Transformer 不建议跳 |
| 65～79 | 已具备 AI 应用基础，重点补原理、Evaluation、Agent Runtime |
| 80～89 | 可以压缩基础课，但必须完成每周工程实验和阶段考试 |
| 90～100 | 基础已较完整，可把精力放在高级 RAG、Agent、Eval、Deployment、Coding Agent |

---

# 7. 薄弱项分析

完成测试后不要只记录总分。

填写：

```text
最薄弱的三个模块：
1.
2.
3.

最薄弱的三个工程能力：
1.
2.
3.

目前最容易“会用但解释不清”的三个知识点：
1.
2.
3.
```

---

# 8. 通过测试不等于可以跳过实验

例如你已经会调用 Embedding API，并不代表你真正理解：

- cosine similarity；
- normalization；
- vector dimension；
- indexing；
- recall；
- reranker；
- embedding model migration。

因此本课程允许“理论快速通过”，但核心实验原则上不跳过。

---

# 9. 完成检查

- [ ] 已在无 AI / 无资料帮助下完成第一次测试。
- [ ] 已记录每一部分分数。
- [ ] 已填写 `PROGRESS.md`。
- [ ] 已识别前三个知识短板。
- [ ] 已识别前三个工程短板。
- [ ] 已确定是否需要调整 18 周学习强度。

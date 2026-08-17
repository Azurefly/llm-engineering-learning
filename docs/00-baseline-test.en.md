# Week 0 — LLM Engineering Baseline Assessment

> Purpose: determine what you already understand, what you only know superficially, and which engineering gaps deserve the most attention before starting the 18-week roadmap.
>
> Rule: complete the first attempt without searching the web and without using AI. Review the answers only after you have recorded your initial score.

Total: 100 points.

---

# 1. Foundational Concepts — 20 Points

Each question is worth 2 points.

Scoring:

- 0: incorrect or unknown
- 1: roughly knows the term but cannot clearly explain the mechanism
- 2: can explain it in your own words and give an engineering example

## Questions

- [ ] 1. What is the relationship between AI, Machine Learning, Deep Learning, and LLMs?
- [ ] 2. What is the difference between training and inference?
- [ ] 3. What is the difference between a model parameter and a hyperparameter?
- [ ] 4. What is a loss function, and why does training need one?
- [ ] 5. What is a gradient, and what does gradient descent do?
- [ ] 6. What are epoch, batch, and batch size?
- [ ] 7. What is overfitting, and how can you detect it?
- [ ] 8. What is a token? Why does one character not necessarily equal one token?
- [ ] 9. What is an embedding, and why can embeddings support semantic search?
- [ ] 10. What is a Transformer, and what major engineering advantage does it have over traditional RNNs?

Score: `__/20`

---

# 2. LLM Principles — 20 Points

Each question is worth 2 points.

- [ ] 1. What does next-token prediction mean?
- [ ] 2. How are logits, probabilities, and softmax related?
- [ ] 3. What behavioral difference would you typically expect between temperature 0 and temperature 1?
- [ ] 4. What do Top-K and Top-P constrain?
- [ ] 5. What problem does self-attention solve?
- [ ] 6. What are Q, K, and V, and why is `QK^T` computed?
- [ ] 7. Why are attention scores divided by `sqrt(d)`?
- [ ] 8. Why does a Transformer need positional information?
- [ ] 9. What does a causal mask do?
- [ ] 10. Explain LLM hallucination from the perspective of probabilistic next-token generation.

Score: `__/20`

---

# 3. LLM Application Development — 20 Points

Task: without using an Agent or RAG framework, implement a minimal Python LLM client.

Suggested location:

```text
baseline/
└── llm_client.py
```

Each item is worth 2 points:

- [ ] Configure `base_url`, `api_key`, and `model`.
- [ ] Send system and user messages.
- [ ] Handle normal non-streaming responses.
- [ ] Handle streaming responses.
- [ ] Configure timeouts.
- [ ] Retry transient failures with a maximum retry count.
- [ ] Record request latency.
- [ ] Read or calculate token usage.
- [ ] Request JSON output and handle parsing failures.
- [ ] Normalize network, authentication, rate-limit, and provider/model errors.

Score: `__/20`

## Additional Questions

These are not scored, but should be written into your notes:

1. Why must retries be bounded?
2. Should HTTP 429 and 5xx errors use exactly the same retry policy?
3. If JSON parsing fails, should you retry the original request, repair the JSON, or reprompt the model? Why?
4. How should logs avoid leaking API keys or sensitive prompts?

---

# 4. RAG / Agent Foundations — 20 Points

Each question is worth 2 points.

- [ ] 1. Describe the complete RAG pipeline.
- [ ] 2. Why can chunk size be neither arbitrarily large nor arbitrarily small?
- [ ] 3. What is the fundamental difference between vector search and SQL `LIKE`?
- [ ] 4. What problems can occur if Top-K is too high or too low?
- [ ] 5. Why can a reranker improve retrieval quality?
- [ ] 6. In tool calling, who actually executes the tool: the model or the application?
- [ ] 7. What is the key difference between an Agent and ordinary chat completion?
- [ ] 8. What should Agent state contain, and what should not be stored indefinitely?
- [ ] 9. Why can Agents enter infinite or repetitive loops?
- [ ] 10. Name at least five engineering controls that can constrain an Agent.

Score: `__/20`

---

# 5. System Design — 20 Points

Design problem:

> Design a Coding Agent that can inspect a Git repository, understand source code, modify code, run tests, and produce a final change summary.

Describe or draw the architecture.

Each item is worth 2 points:

- [ ] 1. Model Layer: model selection and fallback strategy.
- [ ] 2. Context Layer: how relevant code and documentation are selected.
- [ ] 3. Repository Search: files, symbols, and references.
- [ ] 4. Planning: how a complex task is decomposed.
- [ ] 5. Tool Layer: at least read/search/edit/test/git tools.
- [ ] 6. State: task state and observation persistence.
- [ ] 7. Loop Control: max steps, duplicate actions, no-progress detection.
- [ ] 8. Validation: how code changes are checked before acceptance.
- [ ] 9. Test & Recovery: failure analysis, retry, and rollback.
- [ ] 10. Security: shell permissions, sensitive files, Git push, and production-system boundaries.

Score: `__/20`

---

# 6. Final Score

| Area | Max | Score |
|---|---:|---:|
| Foundations | 20 |  |
| LLM Principles | 20 |  |
| LLM Applications | 20 |  |
| RAG / Agent | 20 |  |
| System Design | 20 |  |
| **Total** | **100** |  |

Suggested interpretation:

| Score | Recommendation |
|---:|---|
| 0–29 | Start from Week 1 and do not skip core labs |
| 30–49 | You have fragmented knowledge; complete Weeks 1–4 fully |
| 50–64 | You may review Weeks 1–2 faster, but do not skip Transformer fundamentals |
| 65–79 | You already have application-development foundations; focus on principles, evaluation, and Agent runtime |
| 80–89 | Compress basic reading if necessary, but still complete engineering labs and stage exams |
| 90–100 | Focus more effort on Advanced RAG, Agents, evaluation, deployment, and Coding Agents |

---

# 7. Gap Analysis

Fill in:

```text
Three weakest knowledge areas:
1.
2.
3.

Three weakest engineering capabilities:
1.
2.
3.

Three areas where I can “use it” but cannot clearly explain it:
1.
2.
3.
```

---

# 8. Passing the Test Does Not Mean Skipping the Lab

For example, being able to call an embedding API does not mean you understand:

- cosine similarity
- normalization
- vector dimensions
- indexing
- retrieval recall
- reranking
- embedding-model migration

The roadmap therefore allows faster theory review, but core implementation labs should generally still be completed.

---

# 9. Completion Checklist

- [ ] First attempt completed without AI or external references.
- [ ] All five section scores recorded.
- [ ] `PROGRESS.en.md` updated.
- [ ] Three biggest knowledge gaps identified.
- [ ] Three biggest engineering gaps identified.
- [ ] Weekly learning intensity adjusted if necessary.

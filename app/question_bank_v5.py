from __future__ import annotations

from dataclasses import dataclass

from .exam_system import Question, multiple, o, short, single


@dataclass(frozen=True)
class Scenario:
    topic_zh: str
    topic_en: str
    scenario_zh: str
    scenario_en: str
    best_zh: str
    best_en: str
    controls: tuple[tuple[str, str, str], ...]
    design_zh: str
    design_en: str
    concepts: tuple[tuple[str, ...], ...]


SCENARIOS: dict[str, Scenario] = {
    "week00": Scenario("LLM 方案选型", "LLM solution selection", "团队把经常变化的内部制度硬编码进 Prompt，维护成本越来越高。", "A team hard-codes frequently changing internal policies into prompts and maintenance cost keeps growing.", "把动态知识迁移到可检索知识源，并保留引用与更新流程", "Move changing knowledge to a retrievable source with citations and an update workflow", (("scope","先区分指令、知识与行为适配问题","Separate instruction, knowledge and behavior-adaptation problems"),("evidence","要求回答可追溯到证据","Require answers to trace back to evidence"),("eval","建立固定评测集验证方案变化","Use a fixed eval set to validate architecture changes")), "设计 Prompt、RAG、Fine-tuning 的选择决策树。", "Design a decision tree for choosing prompting, RAG, or fine-tuning.", (("prompt","指令"),("rag","检索","知识"),("fine-tuning","微调","行为"))),
    "week01": Scenario("训练稳定性", "Training stability", "一个小模型训练时 Loss 快速震荡并出现 NaN。", "A small model's loss oscillates and then becomes NaN during training.", "先检查学习率、输入尺度、梯度与数值稳定性", "Inspect learning rate, input scale, gradients, and numerical stability first", (("lr","记录并尝试降低 learning rate","Log and try a lower learning rate"),("grad","监控梯度范数与 NaN/Inf","Monitor gradient norms and NaN/Inf"),("split","确认训练/验证数据划分与分布","Verify train/validation splits and distributions")), "给出一个最小训练异常诊断流程。", "Design a minimal training-failure diagnostic flow.", (("loss","损失"),("gradient","梯度"),("learning rate","学习率"),("validation","验证"))),
    "week02": Scenario("PyTorch 排障", "PyTorch debugging", "训练脚本在 GPU 上报 Expected all tensors to be on the same device。", "A GPU training script reports that all tensors must be on the same device.", "逐个检查模型、输入、标签与新建 Tensor 的 device", "Check the device of the model, inputs, labels, and newly created tensors", (("shape","记录关键 Tensor shape","Log critical tensor shapes"),("dtype","检查 dtype 是否满足算子要求","Check tensor dtypes"),("device","统一 model/input/label device","Align model/input/label devices")), "设计训练循环的 shape、dtype、device 自检策略。", "Design shape, dtype, and device checks for a training loop.", (("shape","维度"),("dtype","类型"),("device","设备"),("assert","断言"))),
    "week03": Scenario("Token 预算", "Token budgeting", "长对话运行一段时间后突然频繁触发 context length exceeded。", "A long-running chat begins to hit context-length-exceeded errors.", "记录 Token 使用并对历史消息做裁剪、摘要或检索式记忆", "Track token usage and trim, summarize, or retrieve conversation memory", (("count","请求前估算输入与输出 token","Estimate input/output tokens before requests"),("history","控制历史消息预算","Budget conversation history"),("fallback","达到阈值时摘要或裁剪","Summarize or trim near the limit")), "设计一个可观测的上下文预算器。", "Design an observable context-budget manager.", (("token","预算"),("context","上下文"),("summary","摘要"),("limit","阈值"))),
    "week04": Scenario("Attention Mask", "Attention masking", "Decoder-only 模型训练后出现明显看到未来标签的泄漏现象。", "A decoder-only model shows evidence of future-token label leakage during training.", "优先检查 causal mask 与目标错位方式", "Inspect the causal mask and target shifting first", (("mask","验证上三角未来位置被屏蔽","Verify future positions are masked"),("shift","检查 next-token target shift","Check next-token target shifting"),("shape","检查 Q/K/V 与 mask 广播 shape","Check Q/K/V and mask broadcast shapes")), "解释如何测试一个自注意力实现没有未来信息泄漏。", "Explain how to test a self-attention implementation for future-information leakage.", (("causal","mask","遮罩"),("future","未来"),("test","测试"))),
    "week05": Scenario("LLM API 可靠性", "LLM API reliability", "生产调用在流量高峰出现间歇性 429 和 5xx。", "Production requests intermittently receive 429 and 5xx errors during peaks.", "对可重试错误实施带抖动的指数退避，并设置总超时与重试上限", "Use jittered exponential backoff for retryable errors with total timeout and retry limits", (("timeout","设置连接与总请求超时","Set connection and total request timeouts"),("retry","区分可重试与不可重试错误","Classify retryable vs non-retryable failures"),("trace","记录 request id、latency、usage","Record request id, latency, and usage")), "设计一个生产级 LLM Client 的失败处理策略。", "Design failure handling for a production LLM client.", (("timeout","超时"),("retry","重试"),("backoff","退避"),("observability","日志","trace"))),
    "week06": Scenario("Tool Calling 安全", "Tool-calling safety", "模型生成了一个删除数据的 Tool Call，但参数缺少必要范围字段。", "The model emits a destructive tool call with a required scope argument missing.", "Schema 校验失败后拒绝执行，并对高风险操作要求显式审批", "Reject execution after schema validation fails and require explicit approval for high-risk actions", (("schema","严格校验参数 schema","Strictly validate argument schemas"),("allowlist","限制可调用工具与作用域","Restrict tools and scopes"),("approval","高风险动作加入 human approval","Require human approval for high-risk actions")), "设计 Tool Runtime 的最小安全边界。", "Design the minimum safety boundary for a tool runtime.", (("validation","schema","校验"),("permission","权限"),("approval","审批"),("timeout","超时"))),
    "week07": Scenario("向量检索", "Vector retrieval", "语义上接近的文档长期排在 Top-K 之外。", "Semantically relevant documents consistently fall outside Top-K.", "检查 embedding 模型、相似度度量、归一化、索引参数与数据切分", "Check the embedding model, similarity metric, normalization, index parameters, and document splitting", (("metric","确认索引与查询使用一致的距离度量","Use a consistent metric for index and query"),("sample","建立带相关性标注的检索样本","Build labeled retrieval examples"),("filter","检查 metadata filter 是否误过滤","Verify metadata filters are not over-restrictive")), "设计向量检索质量的离线评测。", "Design an offline evaluation for vector retrieval quality.", (("recall","召回"),("top-k","top k"),("dataset","数据集"),("metric","指标"))),
    "week08": Scenario("RAG 证据不足", "Insufficient RAG evidence", "Retriever 返回的文档都只有弱相关，但生成模型仍然给出确定答案。", "Retrieved documents are only weakly relevant, yet the model gives a confident answer.", "增加检索阈值、证据检查和 no-answer 分支", "Add retrieval thresholds, evidence checks, and a no-answer branch", (("threshold","设置最低相关性/证据阈值","Set minimum relevance/evidence thresholds"),("citation","输出引用并校验来源","Return and validate citations"),("trace","记录 query、chunks、scores","Trace query, chunks, and scores")), "设计一个能够拒答的基础 RAG 流程。", "Design a basic RAG pipeline that can abstain.", (("retrieve","检索"),("threshold","阈值"),("evidence","证据"),("no-answer","拒答"))),
    "week09": Scenario("高级检索", "Advanced retrieval", "纯向量检索对产品编号、错误码和精确术语表现很差。", "Pure vector retrieval performs poorly on product IDs, error codes, and exact terminology.", "引入 sparse/BM25 与 dense 的 Hybrid Search，再对候选 rerank", "Combine sparse/BM25 and dense retrieval, then rerank candidates", (("hybrid","同时评估 sparse 与 dense 信号","Evaluate sparse and dense signals"),("rerank","对候选集增加 reranker","Add a reranker over candidates"),("rewrite","对复杂查询测试 rewrite/multi-query","Test rewrite or multi-query for complex queries")), "设计 Hybrid Search + Rerank 的检索流水线。", "Design a hybrid-search and reranking pipeline.", (("dense","向量"),("sparse","bm25","关键词"),("rerank","重排"),("fusion","融合"))),
    "week10": Scenario("RAG 回归评测", "RAG regression evaluation", "更换 embedding 后用户感觉效果变差，但团队没有可比较的数据。", "Users report worse results after an embedding change, but the team has no comparable data.", "建立固定 Eval Dataset，并分别评测 retrieval 与 answer 指标", "Build a fixed eval dataset and measure retrieval and answer metrics separately", (("dataset","冻结代表性评测集","Freeze a representative eval dataset"),("retrieval","记录 recall/precision/ranking 指标","Track retrieval metrics"),("answer","记录 faithfulness/relevance 等答案指标","Track answer metrics such as faithfulness/relevance")), "设计一次 RAG 变更的回归门禁。", "Design a regression gate for a RAG change.", (("baseline","基线"),("retrieval","检索指标"),("faithfulness","忠实度"),("threshold","阈值"))),
    "week11": Scenario("Agent Loop", "Agent loops", "Agent 在 search → think → search 间反复循环，没有产生新信息。", "An agent loops between search → think → search without producing new information.", "记录状态并增加 max steps、重复检测和 no-progress 终止条件", "Track state and add max-steps, repetition detection, and no-progress termination", (("state","显式记录 step/state/observation","Track step/state/observation explicitly"),("progress","检测新信息或状态变化","Detect new information or state changes"),("budget","限制 steps/time/token/cost","Bound steps, time, tokens, and cost")), "设计一个最小可控 Agent Loop。", "Design a minimal controllable agent loop.", (("state","状态"),("tool","工具"),("observation","观察"),("stop","终止"))),
    "week12": Scenario("Agent Runtime", "Agent runtime", "Agent 连续三次以同样参数调用同一工具并得到相同错误。", "An agent calls the same tool three times with identical arguments and gets the same error.", "Runtime 应识别重复签名并触发熔断/改计划，而不是无限重试", "The runtime should detect repeated signatures and circuit-break or replan instead of retrying forever", (("signature","记录 tool+arguments+result signature","Track tool+arguments+result signatures"),("circuit","设置 repetition/no-progress circuit breaker","Add repetition/no-progress circuit breakers"),("policy","高风险与失败状态走明确策略","Route risky/failing states through explicit policies")), "设计 Agent Runtime 的死循环保护。", "Design dead-loop protection for an agent runtime.", (("max steps","最大步骤"),("repeat","重复"),("no progress","无进展"),("circuit breaker","熔断"))),
    "week13": Scenario("MCP 集成", "MCP integration", "一个 MCP Server 暴露了过多工具，客户端难以判断能力边界。", "An MCP server exposes too many tools and clients cannot reason about capability boundaries.", "按领域缩小工具集合，提供清晰 schema/description，并区分 tools/resources", "Narrow tools by domain, provide clear schemas/descriptions, and distinguish tools from resources", (("schema","为 tool 输入提供明确 schema","Provide explicit input schemas"),("description","写清用途、限制和副作用","Document purpose, limits, and side effects"),("transport","对 stdio/HTTP transport 做连接测试","Test stdio/HTTP transports")), "设计一个最小 MCP Server 的能力边界。", "Design capability boundaries for a minimal MCP server.", (("tools","工具"),("resources","资源"),("schema","模式"),("transport","传输"))),
    "week14": Scenario("模型路由", "Model routing", "主模型供应商抖动导致整个应用不可用，且业务代码写死了模型 ID。", "A primary provider outage breaks the app because model IDs are hard-coded in business code.", "使用逻辑模型组、健康检查、fallback 与超时策略解耦 Provider", "Use logical model groups, health checks, fallbacks, and timeouts to decouple providers", (("logical","业务只依赖 logical model group","Make business code depend on logical groups"),("fallback","配置 provider/model fallback","Configure provider/model fallbacks"),("policy","按质量、成本、延迟、隐私路由","Route on quality, cost, latency, and privacy")), "设计一个多模型 Gateway 的路由与降级策略。", "Design routing and degradation for a multi-model gateway.", (("router","路由"),("fallback","降级"),("latency","延迟"),("cost","成本"),("privacy","隐私"))),
    "week15": Scenario("LLM 安全与可观测", "LLM security and observability", "RAG 检索到的网页中包含提示模型忽略系统规则的恶意文本。", "A retrieved webpage contains malicious text telling the model to ignore system rules.", "把外部内容视为不可信数据，并限制其影响范围与可调用工具权限", "Treat external content as untrusted data and restrict its influence and tool permissions", (("trace","记录输入来源、模型和工具 trace","Trace input provenance, model, and tools"),("permission","工具执行遵循最小权限","Use least privilege for tools"),("eval","维护 prompt-injection 安全测试集","Maintain prompt-injection security evals")), "设计一套 Prompt Injection 防护与回归验证。", "Design prompt-injection defenses and regression validation.", (("untrusted","不可信"),("permission","权限"),("injection","注入"),("eval","评测"))),
    "week16": Scenario("推理性能", "Inference performance", "本地服务首 Token 很慢且长上下文并发时频繁 OOM。", "A local service has slow first-token latency and OOMs under concurrent long-context requests.", "分别测 TTFT、TPS、并发、KV Cache 与显存，再决定量化/批处理/上下文策略", "Measure TTFT, TPS, concurrency, KV cache, and memory before choosing quantization, batching, or context policies", (("ttft","分离 TTFT 与生成吞吐","Separate TTFT from generation throughput"),("memory","记录模型权重与 KV cache 显存","Track weight and KV-cache memory"),("load","用不同 context/concurrency 做压测","Load-test multiple context and concurrency levels")), "设计本地 LLM 服务的性能基准。", "Design a benchmark for a local LLM service.", (("ttft","首 token"),("tps","吞吐"),("memory","显存"),("concurrency","并发"))),
    "week17": Scenario("微调决策", "Fine-tuning decisions", "团队希望通过 LoRA 让模型记住每天变化的内部价格表。", "A team wants LoRA to make a model memorize an internal price list that changes daily.", "先用 RAG/工具访问动态事实；微调更适合稳定的行为、格式或任务适配", "Use RAG/tools for changing facts; fine-tuning is better for stable behavior, format, or task adaptation", (("data","明确训练数据目标与质量","Define training-data goals and quality"),("baseline","先建立未微调基线","Establish a pre-tuning baseline"),("eval","用独立评测集检查收益和退化","Use held-out evals for gains and regressions")), "设计 Fine-tuning 是否值得做的决策流程。", "Design a decision flow for whether fine-tuning is justified.", (("rag","检索"),("behavior","行为"),("data","数据"),("eval","评测"))),
    "week18": Scenario("Coding Agent 发布闭环", "Coding-agent release loop", "Coding Agent 修改了多个文件并声称完成，但没有展示测试结果和 diff。", "A coding agent edits several files and claims completion without showing tests or a diff.", "要求 inspect → patch → test/build → diff review → approval/release 的可验证闭环", "Require a verifiable inspect → patch → test/build → diff review → approval/release loop", (("scope","修改前确认范围与相关代码","Confirm scope and relevant code before editing"),("test","修改后运行适当测试/构建","Run appropriate tests/builds after edits"),("diff","审查 diff 与意外改动","Review diffs and unintended changes")), "设计 Coding Agent 从任务到可发布变更的最小状态机。", "Design a minimal state machine from coding task to releasable change.", (("inspect","检查"),("patch","修改"),("test","测试"),("review","审查"),("release","发布"))),
}


def _build(lesson_key: str, spec: Scenario) -> tuple[Question, ...]:
    prefix = lesson_key.replace("week", "w")
    return (
        single(
            f"{prefix}a1",
            f"工程场景：{spec.scenario_zh} 最合理的第一步是什么？",
            f"Engineering scenario: {spec.scenario_en} What is the best first step?",
            (
                o("a", spec.best_zh, spec.best_en),
                o("b", "先增加重试次数并忽略根因", "Increase retries first and ignore the root cause"),
                o("c", "修改与问题无关的界面代码", "Change unrelated UI code"),
                o("d", "关闭所有校验和日志", "Disable all validation and logging"),
            ),
            "a",
            20,
        ),
        multiple(
            f"{prefix}a2",
            f"围绕“{spec.topic_zh}”进行工程排障/治理时，应优先包含哪些动作？",
            f"Which actions belong in engineering diagnostics/governance for {spec.topic_en}?",
            tuple(o(value, zh, en) for value, zh, en in spec.controls)
            + (o("skip", "跳过度量，直接凭感觉上线", "Skip measurement and deploy by intuition"),),
            tuple(value for value, _, _ in spec.controls),
            20,
        ),
        short(f"{prefix}a3", spec.design_zh, spec.design_en, spec.concepts, 25),
    )


APPLICATION_QUESTIONS: dict[str, tuple[Question, ...]] = {key: _build(key, spec) for key, spec in SCENARIOS.items()}


def extra_for(lesson_key: str) -> tuple[Question, ...]:
    return APPLICATION_QUESTIONS.get(lesson_key, ())

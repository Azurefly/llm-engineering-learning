from __future__ import annotations

import json
import os
import random
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .course import LESSONS, LESSON_MAP, title_for
from .db import Database, now_iso
from .exam_system import (
    EXAMS,
    Exam,
    Question,
    correct_text,
    grade_question,
    multiple,
    o,
    short,
    single,
)
from .i18n import normalize_lang, tr

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
DATA_DIR = Path(os.getenv("LLM_LEARNING_DATA_DIR", str(REPO_ROOT / "data")))
DB_PATH = DATA_DIR / "learning.db"

templates = Jinja2Templates(directory=APP_DIR / "templates")
db = Database(DB_PATH)
router = APIRouter()


@dataclass(frozen=True)
class Stage:
    key: str
    weeks: tuple[str, ...]
    zh: str
    en: str
    pass_score: int = 80
    question_count: int = 12


WEEK_TAGS: dict[str, tuple[str, ...]] = {
    "week00": ("LLM基础", "RAG", "Agent"),
    "week01": ("数学基础", "机器学习"),
    "week02": ("神经网络", "PyTorch"),
    "week03": ("Tokenizer", "采样", "Context Window"),
    "week04": ("Transformer", "Attention"),
    "week05": ("LLM API", "Prompt Engineering"),
    "week06": ("Structured Output", "Tool Calling"),
    "week07": ("Embedding", "Vector Search"),
    "week08": ("RAG", "Chunking", "Retrieval"),
    "week09": ("Hybrid Search", "Reranker", "Query Rewrite"),
    "week10": ("RAG Evaluation", "Faithfulness"),
    "week11": ("Agent", "ReAct", "Workflow"),
    "week12": ("Agent Runtime", "Guardrails"),
    "week13": ("MCP", "Tools", "Resources"),
    "week14": ("LiteLLM", "Model Router"),
    "week15": ("Evaluation", "Observability", "Security"),
    "week16": ("Inference", "Quantization", "vLLM"),
    "week17": ("Fine-tuning", "LoRA", "QLoRA"),
    "week18": ("Coding Agent", "Testing", "Release"),
}


def _extra_questions() -> dict[str, tuple[Question, ...]]:
    return {
        "week03": (
            single("w03x1", "BPE 的主要工程价值更接近哪一项？", "What is a key engineering value of BPE?", (
                o("a", "把所有文本固定切成单字符", "Force all text into characters"),
                o("b", "在词表规模与未知词处理之间取得折中", "Balance vocabulary size and unknown-word handling"),
                o("c", "替代模型推理", "Replace inference"),
                o("d", "只压缩磁盘文件", "Only compress files"),
            ), "b", 20),
            multiple("w03x2", "哪些因素会直接影响一次请求的 Token 预算？", "Which factors directly affect a request's token budget?", (
                o("prompt", "输入 Prompt", "Input prompt"),
                o("history", "对话历史", "Conversation history"),
                o("output", "计划输出长度", "Planned output length"),
                o("db", "SQLite 页大小", "SQLite page size"),
            ), ("prompt", "history", "output"), 20),
            short("w03x3", "说明 Temperature 与 Top-P 的区别，以及为什么通常不需要同时把两者都调得非常激进。", "Explain the difference between Temperature and Top-P, and why both usually should not be tuned aggressively at the same time.", (
                ("temperature", "温度", "logit", "随机性"),
                ("top-p", "top p", "nucleus", "候选概率质量"),
                ("tradeoff", "稳定", "不可控", "组合", "权衡"),
            ), 25),
        ),
        "week04": (
            single("w04x1", "Scaled Dot-Product Attention 中除以 √d 的主要目的是什么？", "Why divide by sqrt(d) in scaled dot-product attention?", (
                o("a", "避免点积过大导致 Softmax 过度饱和", "Avoid overly large dot products saturating softmax"),
                o("b", "减少词表大小", "Reduce vocabulary size"),
                o("c", "生成位置编码", "Generate positional encoding"),
                o("d", "替代 LayerNorm", "Replace LayerNorm"),
            ), "a", 20),
            multiple("w04x2", "一个典型 Transformer Block 常包含哪些组成？", "Which components are common in a Transformer block?", (
                o("attn", "多头注意力", "Multi-head attention"),
                o("ffn", "前馈网络", "Feed-forward network"),
                o("residual", "残差连接", "Residual connection"),
                o("txn", "数据库事务", "Database transaction"),
            ), ("attn", "ffn", "residual"), 20),
            short("w04x3", "解释 Causal Self-Attention 为什么适合 Decoder-only 语言模型。", "Explain why causal self-attention fits decoder-only language models.", (
                ("future", "未来", "mask", "遮罩"),
                ("next token", "下一个token", "自回归", "autoregressive"),
                ("context", "历史上下文", "前文"),
            ), 25),
        ),
        "week05": (
            single("w05x1", "下列哪种情况最适合自动 Retry？", "Which case is most appropriate for automatic retry?", (
                o("a", "持续性的 400 参数错误", "Persistent 400 bad request"),
                o("b", "临时 429/5xx 或网络抖动", "Transient 429/5xx or network failure"),
                o("c", "Prompt 逻辑错误", "Prompt logic error"),
                o("d", "用户取消请求", "User cancellation"),
            ), "b", 20),
            multiple("w05x2", "生产级 LLM Client 应优先具备哪些能力？", "Which capabilities should a production LLM client prioritize?", (
                o("timeout", "Timeout", "Timeout"),
                o("retry", "Retry/Backoff", "Retry/backoff"),
                o("usage", "Token/Usage 统计", "Token/usage tracking"),
                o("trace", "请求日志/Trace", "Request logging/trace"),
            ), ("timeout", "retry", "usage", "trace"), 20),
            short("w05x3", "说明 System、User、Few-shot 示例在 Prompt 中分别承担什么角色。", "Explain the roles of System, User, and few-shot examples in a prompt.", (
                ("system", "系统", "高优先级", "规则"),
                ("user", "用户", "任务", "输入"),
                ("example", "few-shot", "示例", "格式"),
            ), 25),
        ),
        "week06": (
            single("w06x1", "JSON Schema 在 Structured Output 中最主要解决什么？", "What does JSON Schema primarily solve in structured output?", (
                o("a", "定义并验证输出结构", "Define and validate output structure"),
                o("b", "替代模型", "Replace the model"),
                o("c", "执行 Shell", "Execute shell"),
                o("d", "建立向量索引", "Build vector indexes"),
            ), "a", 20),
            multiple("w06x2", "Tool Calling 的安全执行层应包含哪些措施？", "Which controls belong in a safe tool-calling execution layer?", (
                o("schema", "参数 Schema 校验", "Argument schema validation"),
                o("allow", "Tool allowlist/权限", "Tool allowlist/permissions"),
                o("timeout", "Timeout", "Timeout"),
                o("blind", "忽略参数直接执行", "Blind execution"),
            ), ("schema", "allow", "timeout"), 20),
            short("w06x3", "描述从用户请求到 Tool Result 再到最终回答的完整调用链。", "Describe the full chain from user request to tool result to final answer.", (
                ("model", "llm", "模型"),
                ("tool call", "工具调用", "arguments", "参数"),
                ("execute", "执行", "runtime", "应用"),
                ("result", "observation", "结果"),
                ("final", "最终回答", "answer"),
            ), 25),
        ),
        "week07": (
            single("w07x1", "Cosine Similarity 更关注向量的什么属性？", "What does cosine similarity mainly focus on?", (
                o("a", "方向夹角", "Direction/angle"), o("b", "磁盘路径", "Disk path"),
                o("c", "数据库事务", "Database transaction"), o("d", "Batch 数", "Batch count"),
            ), "a", 20),
            multiple("w07x2", "向量检索工程中常见的设计项有哪些？", "Which are common vector-search design concerns?", (
                o("dim", "向量维度", "Vector dimension"), o("metric", "相似度度量", "Similarity metric"),
                o("filter", "Metadata Filter", "Metadata filter"), o("index", "索引策略", "Index strategy"),
            ), ("dim", "metric", "filter", "index"), 20),
            short("w07x3", "说明精确检索与 ANN 近似最近邻检索的主要权衡。", "Explain the main tradeoff between exact search and ANN approximate nearest-neighbor search.", (
                ("accuracy", "准确", "召回"), ("speed", "速度", "延迟"), ("scale", "规模", "大数据"),
            ), 25),
        ),
        "week08": (
            single("w08x1", "Chunk 过大最可能带来什么问题？", "What is a likely issue with overly large chunks?", (
                o("a", "检索粒度变粗并带入更多无关上下文", "Coarser retrieval and more irrelevant context"),
                o("b", "Token 永远更少", "Always fewer tokens"), o("c", "一定提升 Recall", "Always improve recall"),
                o("d", "完全消除幻觉", "Eliminate hallucination"),
            ), "a", 20),
            multiple("w08x2", "为了让 RAG 可追溯，应保存哪些字段？", "Which fields help make RAG traceable?", (
                o("source", "source", "source"), o("chunk", "chunk_id", "chunk_id"),
                o("score", "retrieval score", "retrieval score"), o("request", "request/query id", "request/query id"),
            ), ("source", "chunk", "score", "request"), 20),
            short("w08x3", "设计一个证据不足时的 No-Answer 策略。", "Design a no-answer strategy for insufficient evidence.", (
                ("threshold", "阈值", "score"), ("evidence", "证据", "context"),
                ("refuse", "无法回答", "不确定", "拒答"), ("source", "引用", "来源"),
            ), 25),
        ),
        "week09": (
            single("w09x1", "Reranker 通常放在检索流程的哪个位置？", "Where is a reranker typically placed?", (
                o("a", "初筛候选之后、送入 LLM 之前", "After candidate retrieval and before the LLM"),
                o("b", "模型训练之前", "Before model training"), o("c", "Docker 构建时", "During Docker build"),
                o("d", "数据库提交之后", "After DB commit"),
            ), "a", 20),
            multiple("w09x2", "Hybrid Search 常组合哪些信号？", "Which signals are commonly combined in hybrid search?", (
                o("dense", "Dense Vector", "Dense vector"), o("sparse", "BM25/关键词", "BM25/keyword"),
                o("meta", "Metadata Filter", "Metadata filter"), o("random", "随机排序", "Random ranking"),
            ), ("dense", "sparse", "meta"), 20),
            short("w09x3", "比较 Query Rewrite 与 Multi-Query 的用途。", "Compare the purposes of query rewrite and multi-query retrieval.", (
                ("rewrite", "改写", "明确", "规范化"), ("multi", "多查询", "多个角度", "扩展"), ("recall", "召回"),
            ), 25),
        ),
        "week10": (
            single("w10x1", "Faithfulness 最关注什么？", "What does faithfulness focus on?", (
                o("a", "回答是否由给定证据支持", "Whether the answer is supported by provided evidence"),
                o("b", "页面配色", "Page color"), o("c", "模型参数量", "Parameter count"), o("d", "Docker 镜像大小", "Docker image size"),
            ), "a", 20),
            multiple("w10x2", "一个可回归的 RAG Eval Dataset 通常应包含哪些信息？", "What should a regression-friendly RAG eval dataset contain?", (
                o("question", "问题", "Question"), o("expected", "期望答案/要点", "Expected answer/key points"),
                o("source", "期望来源", "Expected sources"), o("category", "类别/难度", "Category/difficulty"),
            ), ("question", "expected", "source", "category"), 20),
            short("w10x3", "为什么必须把 Retrieval 指标与最终 Answer 指标分开评测？", "Why should retrieval metrics and final-answer metrics be evaluated separately?", (
                ("retrieval", "检索", "召回"), ("generation", "回答", "生成"), ("diagnose", "定位", "诊断", "归因"),
            ), 25),
        ),
        "week11": (
            single("w11x1", "Agent Loop 中 Observation 通常表示什么？", "What does Observation usually mean in an agent loop?", (
                o("a", "工具执行返回的结果", "The result returned by tool execution"), o("b", "模型参数", "Model parameters"),
                o("c", "Tokenizer 词表", "Tokenizer vocabulary"), o("d", "CSS 样式", "CSS style"),
            ), "a", 20),
            multiple("w11x2", "一个最小 Agent Loop 通常包含哪些元素？", "Which elements belong in a minimal agent loop?", (
                o("goal", "Goal/State", "Goal/state"), o("action", "Action/Tool Call", "Action/tool call"),
                o("obs", "Observation", "Observation"), o("stop", "停止条件", "Stop condition"),
            ), ("goal", "action", "obs", "stop"), 20),
            short("w11x3", "说明确定性 Workflow 与自主 Agent 的边界和适用场景。", "Explain the boundary and use cases of deterministic workflows versus autonomous agents.", (
                ("deterministic", "确定性", "固定流程"), ("agent", "自主", "动态决策"), ("risk", "风险", "可控", "适用"),
            ), 25),
        ),
        "week12": (
            single("w12x1", "Circuit Breaker 更适合解决哪类问题？", "What problem is a circuit breaker best suited for?", (
                o("a", "持续失败时快速停止继续调用下游", "Stop repeated downstream calls during persistent failures"),
                o("b", "增加 Tokenizer 词表", "Increase tokenizer vocabulary"), o("c", "提高屏幕亮度", "Increase screen brightness"),
                o("d", "替代所有 Retry", "Replace every retry"),
            ), "a", 20),
            multiple("w12x2", "生产 Agent 常见 Guardrail 有哪些？", "Which are common production-agent guardrails?", (
                o("steps", "Max Steps", "Max steps"), o("budget", "Token/Cost Budget", "Token/cost budget"),
                o("approval", "Human Approval", "Human approval"), o("loop", "Duplicate/No-progress Detection", "Duplicate/no-progress detection"),
            ), ("steps", "budget", "approval", "loop"), 20),
            short("w12x3", "如何判断 Agent 处于“有动作但没有进展”的循环？", "How can you detect an agent loop with activity but no meaningful progress?", (
                ("repeat", "重复", "相同动作"), ("state", "状态", "目标"),
                ("progress", "进展", "变化"), ("threshold", "阈值", "次数", "终止"),
            ), 25),
        ),
        "week13": (
            single("w13x1", "MCP Client 的职责更接近哪项？", "What is closest to the role of an MCP client?", (
                o("a", "连接 MCP Server 并发现/调用其能力", "Connect to MCP servers and discover/invoke capabilities"),
                o("b", "训练基础模型", "Train foundation models"), o("c", "替代操作系统", "Replace the OS"),
                o("d", "只负责向量检索", "Only perform vector retrieval"),
            ), "a", 20),
            multiple("w13x2", "MCP Server 可暴露哪些核心 Primitive？", "Which core primitives can an MCP server expose?", (
                o("tools", "Tools", "Tools"), o("resources", "Resources", "Resources"),
                o("prompts", "Prompts", "Prompts"), o("gpu", "GPU Driver", "GPU driver"),
            ), ("tools", "resources", "prompts"), 20),
            short("w13x3", "说明 MCP 与模型原生 Tool Calling 的区别与配合关系。", "Explain the difference and relationship between MCP and model-native tool calling.", (
                ("protocol", "协议", "标准化", "连接"), ("tool calling", "工具调用", "模型"),
                ("server", "client", "服务端", "客户端"),
            ), 25),
        ),
        "week14": (
            single("w14x1", "Fallback 的主要作用是什么？", "What is the main purpose of fallback?", (
                o("a", "主模型不可用时切换备用模型/部署", "Switch to a backup model/deployment when the primary fails"),
                o("b", "删除日志", "Delete logs"), o("c", "替代所有评测", "Replace all evaluations"), o("d", "增加词表", "Increase vocabulary"),
            ), "a", 20),
            multiple("w14x2", "Model Router 做决策时可以考虑哪些输入？", "Which inputs can a model router consider?", (
                o("capability", "模型能力/任务类型", "Capability/task type"), o("cost", "成本", "Cost"),
                o("latency", "延迟", "Latency"), o("privacy", "隐私/本地化要求", "Privacy/locality requirements"),
            ), ("capability", "cost", "latency", "privacy"), 20),
            short("w14x3", "为什么业务层应优先依赖 fast/reasoning/coding 等逻辑模型名，而不是硬编码 Provider 型号？", "Why should applications prefer logical model groups such as fast/reasoning/coding instead of hard-coding provider model IDs?", (
                ("decouple", "解耦", "耦合"), ("switch", "切换", "替换", "fallback"), ("policy", "策略", "路由"),
            ), 25),
        ),
        "week15": (
            single("w15x1", "Prompt Injection 可能来自哪里？", "Where can prompt injection originate?", (
                o("a", "用户输入或被检索/读取的外部内容", "User input or retrieved/read external content"),
                o("b", "只能来自 System Prompt", "Only the system prompt"), o("c", "只能来自 GPU", "Only the GPU"), o("d", "不会发生", "It cannot happen"),
            ), "a", 20),
            multiple("w15x2", "Agent Trace 值得记录哪些字段？", "Which fields are useful in an agent trace?", (
                o("model", "model", "model"), o("tool", "tool + arguments", "tool + arguments"),
                o("usage", "token/cost/latency", "token/cost/latency"), o("status", "step/error/final status", "step/error/final status"),
            ), ("model", "tool", "usage", "status"), 20),
            short("w15x3", "说明最小权限与 Human Approval 如何共同降低高风险 Tool 的危害。", "Explain how least privilege and human approval jointly reduce high-risk tool damage.", (
                ("least privilege", "最小权限", "权限"), ("approval", "审批", "human"), ("high risk", "高风险", "删除", "生产"),
            ), 25),
        ),
        "week16": (
            single("w16x1", "TTFT 指标表示什么？", "What does TTFT measure?", (
                o("a", "从请求到首个 Token 的时间", "Time from request to first token"), o("b", "训练总时长", "Total training time"),
                o("c", "文件传输时间", "File transfer time"), o("d", "数据库锁等待", "DB lock wait"),
            ), "a", 20),
            multiple("w16x2", "哪些因素通常会增加推理显存压力？", "Which factors commonly increase inference memory pressure?", (
                o("context", "更长 Context", "Longer context"), o("concurrency", "更高并发", "Higher concurrency"),
                o("model", "更大模型/更高精度权重", "Larger model/higher-precision weights"),
                o("none", "关闭日志一定增加显存", "Disabling logs always increases VRAM"),
            ), ("context", "concurrency", "model"), 20),
            short("w16x3", "说明量化带来的主要收益与风险。", "Explain the main benefits and risks of quantization.", (
                ("memory", "显存", "内存", "更小"), ("speed", "速度", "吞吐"), ("quality", "精度", "质量", "损失"),
            ), 25),
        ),
        "week17": (
            single("w17x1", "LoRA 的核心思想是什么？", "What is the core idea of LoRA?", (
                o("a", "冻结大部分原参数并训练低秩适配参数", "Freeze most base weights and train low-rank adapters"),
                o("b", "删除所有模型参数", "Delete all model parameters"), o("c", "只做向量检索", "Only do vector search"), o("d", "替代数据集", "Replace the dataset"),
            ), "a", 20),
            multiple("w17x2", "哪些场景更适合优先考虑 RAG 而不是 Fine-tuning？", "Which cases often favor RAG before fine-tuning?", (
                o("fresh", "知识需要频繁更新", "Knowledge changes frequently"), o("private", "私有文档事实问答", "Private-document factual QA"),
                o("citation", "需要引用来源", "Source citation is required"), o("style", "只改变固定输出风格", "Only a fixed output style change"),
            ), ("fresh", "private", "citation"), 20),
            short("w17x3", "比较 LoRA 与 QLoRA：二者共同点和 QLoRA 的额外思路是什么？", "Compare LoRA and QLoRA: what do they share, and what extra idea does QLoRA add?", (
                ("lora", "低秩", "adapter", "适配"), ("quant", "量化", "4bit", "4-bit"), ("memory", "显存", "内存"),
            ), 25),
        ),
        "week18": (
            single("w18x1", "Repository Map 对 Coding Agent 的主要价值是什么？", "What is the main value of a repository map for a coding agent?", (
                o("a", "用紧凑结构帮助模型定位重要符号和文件关系", "Compactly expose important symbols and file relationships"),
                o("b", "替代所有测试", "Replace all tests"), o("c", "隐藏代码", "Hide code"), o("d", "只统计行数", "Only count lines"),
            ), "a", 20),
            multiple("w18x2", "一个可靠 Coding Agent 的修改闭环通常包含哪些步骤？", "Which steps belong in a reliable coding-agent change loop?", (
                o("search", "搜索/读取相关代码", "Search/read relevant code"), o("patch", "最小修改/Patch", "Minimal modification/patch"),
                o("test", "构建/测试", "Build/test"), o("diff", "审查 Diff", "Review diff"),
            ), ("search", "patch", "test", "diff"), 20),
            short("w18x3", "设计从代码修改到发布前的最小安全验证链。", "Design a minimal safe validation chain from code modification to pre-release.", (
                ("compile", "build", "构建", "编译"), ("test", "测试"), ("diff", "review", "审查"), ("approval", "审批", "发布", "release"),
            ), 25),
        ),
    }


EXTRA_QUESTIONS = _extra_questions()

STAGES: tuple[Stage, ...] = (
    Stage("stage01", ("week00", "week01", "week02", "week03", "week04"), "阶段一：基础原理", "Stage 1: Foundations", 75, 12),
    Stage("stage02", ("week05", "week06", "week07", "week08"), "阶段二：LLM 应用与基础 RAG", "Stage 2: LLM Apps & Basic RAG", 80, 12),
    Stage("stage03", ("week09", "week10", "week11", "week12"), "阶段三：高级 RAG 与 Agent", "Stage 3: Advanced RAG & Agents", 80, 12),
    Stage("stage04", ("week13", "week14", "week15", "week16"), "阶段四：平台、治理与部署", "Stage 4: Platform, Governance & Deployment", 80, 12),
    Stage("stage05", ("week17", "week18"), "阶段五：高级与毕业综合", "Stage 5: Advanced & Capstone", 80, 10),
)
STAGE_MAP = {s.key: s for s in STAGES}


def bank_for(lesson_key: str) -> list[Question]:
    base = list(EXAMS.get(lesson_key, Exam(lesson_key, "", "", ())).questions)
    return base + list(EXTRA_QUESTIONS.get(lesson_key, ()))


def all_questions() -> dict[str, tuple[str, Question]]:
    result: dict[str, tuple[str, Question]] = {}
    for lesson in LESSONS:
        for q in bank_for(lesson.key):
            result[q.id] = (lesson.key, q)
    return result


QUESTION_INDEX = all_questions()


def difficulty_for(q: Question) -> str:
    if q.kind == "short":
        return "hard"
    if q.kind in {"single", "multiple"}:
        return "medium"
    return "easy"


def knowledge_for(lesson_key: str, q: Question) -> tuple[str, ...]:
    tags = WEEK_TAGS.get(lesson_key, ())
    if q.kind == "short" and len(tags) > 1:
        return tags[:3]
    return tags[:2]


def init_tables() -> None:
    with db.connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS exam_v2_meta(
                attempt_id INTEGER PRIMARY KEY,
                mode TEXT NOT NULL,
                scope_key TEXT NOT NULL,
                title_zh TEXT NOT NULL,
                title_en TEXT NOT NULL,
                seed INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS exam_attempt_questions(
                attempt_id INTEGER NOT NULL,
                seq INTEGER NOT NULL,
                lesson_key TEXT NOT NULL,
                question_id TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                knowledge_json TEXT NOT NULL DEFAULT '[]',
                PRIMARY KEY(attempt_id, seq)
            );
            CREATE INDEX IF NOT EXISTS idx_exam_attempt_questions_qid
                ON exam_attempt_questions(question_id);
            """
        )


init_tables()


def _lang(request: Request) -> str:
    return normalize_lang(request.query_params.get("lang") or request.cookies.get("lang"))


def _nav(request: Request, lang: str) -> dict[str, Any]:
    progress = db.all_progress()
    lessons = [
        {
            "key": l.key,
            "week": l.week,
            "title": title_for(l, lang),
            "progress": progress.get(l.key, {"status": "not_started", "percent": 0, "score": None}),
        }
        for l in LESSONS
    ]
    return {
        "request": request,
        "lang": lang,
        "t": lambda key: tr(lang, key),
        "lessons": lessons,
        "current_path": request.url.path,
    }


def _choose_balanced(items: list[tuple[str, Question]], count: int, seed: int) -> list[tuple[str, Question]]:
    rng = random.Random(seed)
    groups: dict[str, list[tuple[str, Question]]] = {"easy": [], "medium": [], "hard": []}
    for item in items:
        groups[difficulty_for(item[1])].append(item)
    for values in groups.values():
        rng.shuffle(values)

    if count <= 0:
        return []
    desired = {"easy": max(1, count // 2), "medium": max(1, count // 3), "hard": 1}
    selected: list[tuple[str, Question]] = []
    for level in ("easy", "medium", "hard"):
        take = min(desired[level], len(groups[level]), max(0, count - len(selected)))
        selected.extend(groups[level][:take])
        groups[level] = groups[level][take:]

    remaining = [item for level in ("easy", "medium", "hard") for item in groups[level]]
    rng.shuffle(remaining)
    selected.extend(remaining[: max(0, count - len(selected))])
    rng.shuffle(selected)
    return selected[:count]


def _choose_stage(stage: Stage, seed: int) -> list[tuple[str, Question]]:
    rng = random.Random(seed)
    per_week: dict[str, list[tuple[str, Question]]] = {}
    for key in stage.weeks:
        values = [(key, q) for q in bank_for(key)]
        rng.shuffle(values)
        per_week[key] = values

    target = stage.question_count
    selected: list[tuple[str, Question]] = []
    base_take = max(1, target // len(stage.weeks))
    for key in stage.weeks:
        selected.extend(per_week[key][:base_take])
        per_week[key] = per_week[key][base_take:]

    remaining = [item for key in stage.weeks for item in per_week[key]]
    rng.shuffle(remaining)
    selected.extend(remaining[: max(0, target - len(selected))])
    rng.shuffle(selected)
    return selected[:target]


def _create_attempt(*, lesson_key: str, lang: str, mode: str, scope_key: str, title_zh: str, title_en: str, selected: list[tuple[str, Question]], pass_score: int, seed: int) -> int:
    with db.connect() as conn:
        cur = conn.execute(
            """INSERT INTO exam_attempts(lesson_key,language,status,started_at,max_score,pass_score)
               VALUES(?,?,?,?,?,?)""",
            (lesson_key, lang, "started", now_iso(), sum(q.points for _, q in selected), pass_score),
        )
        attempt_id = int(cur.lastrowid)
        conn.execute(
            """INSERT INTO exam_v2_meta(attempt_id,mode,scope_key,title_zh,title_en,seed,created_at)
               VALUES(?,?,?,?,?,?,?)""",
            (attempt_id, mode, scope_key, title_zh, title_en, seed, now_iso()),
        )
        for seq, (source_lesson, q) in enumerate(selected, 1):
            conn.execute(
                """INSERT INTO exam_attempt_questions(attempt_id,seq,lesson_key,question_id,difficulty,knowledge_json)
                   VALUES(?,?,?,?,?,?)""",
                (attempt_id, seq, source_lesson, q.id, difficulty_for(q), json.dumps(knowledge_for(source_lesson, q), ensure_ascii=False)),
            )
    return attempt_id


def _attempt(attempt_id: int) -> dict[str, Any] | None:
    with db.connect() as conn:
        row = conn.execute(
            """SELECT a.*,m.mode,m.scope_key,m.title_zh,m.title_en,m.seed
               FROM exam_attempts a LEFT JOIN exam_v2_meta m ON m.attempt_id=a.id WHERE a.id=?""",
            (attempt_id,),
        ).fetchone()
    return dict(row) if row else None


def _selected_questions(attempt_id: int) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT seq,lesson_key,question_id,difficulty,knowledge_json
               FROM exam_attempt_questions WHERE attempt_id=? ORDER BY seq""",
            (attempt_id,),
        ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        indexed = QUESTION_INDEX.get(item["question_id"])
        if not indexed:
            continue
        item["question"] = indexed[1]
        item["knowledge"] = json.loads(item.pop("knowledge_json"))
        result.append(item)
    return result


def _question_view(item: dict[str, Any], lang: str) -> dict[str, Any]:
    q: Question = item["question"]
    en = lang == "en"
    return {
        "seq": item["seq"], "lesson_key": item["lesson_key"], "id": q.id, "type": q.kind,
        "points": q.points, "prompt": q.en if en else q.zh,
        "options": [{"value": v, "label": e if en else z} for v, z, e in q.options],
        "difficulty": item["difficulty"], "knowledge": item["knowledge"],
    }


def _display_answer(answer: Any) -> str:
    if isinstance(answer, list):
        return ", ".join(str(x) for x in answer)
    return str(answer or "")


def _save_submission(attempt: dict[str, Any], answers: dict[str, Any], selected: list[dict[str, Any]]) -> dict[str, Any]:
    details = []
    for item in selected:
        q: Question = item["question"]
        detail = grade_question(q, answers.get(q.id))
        detail.update({"lesson_key": item["lesson_key"], "difficulty": item["difficulty"], "knowledge": item["knowledge"]})
        details.append(detail)

    score = round(sum(d["earned"] for d in details), 2)
    max_score = round(sum(d["max_points"] for d in details), 2)
    percent = round(score / max_score * 100, 2) if max_score else 0.0
    pass_score = float(attempt.get("pass_score") or 80)
    passed = percent >= pass_score

    with db.connect() as conn:
        conn.execute(
            """UPDATE exam_attempts SET status='submitted',submitted_at=?,score=?,max_score=?,percent=?,passed=?,pass_score=? WHERE id=?""",
            (now_iso(), score, max_score, percent, 1 if passed else 0, pass_score, attempt["id"]),
        )
        conn.execute("DELETE FROM exam_answers WHERE attempt_id=?", (attempt["id"],))
        for detail in details:
            qid = detail["question_id"]
            conn.execute(
                """INSERT INTO exam_answers(attempt_id,question_id,answer_json,earned,max_points,correct,feedback_json)
                   VALUES(?,?,?,?,?,?,?)""",
                (attempt["id"], qid, json.dumps(answers.get(qid), ensure_ascii=False), detail["earned"], detail["max_points"],
                 1 if detail["correct"] else 0,
                 json.dumps({"matched": detail["matched"], "missing": detail["missing"], "difficulty": detail["difficulty"], "knowledge": detail["knowledge"]}, ensure_ascii=False)),
            )

    if attempt.get("mode") == "weekly" and attempt.get("scope_key") in LESSON_MAP:
        lesson_key = attempt["scope_key"]
        current = db.all_progress().get(lesson_key, {"percent": 0, "status": "not_started", "score": None})
        best_score = max(float(current.get("score") or 0), percent)
        if passed:
            db.set_progress(lesson_key, "completed", 100, best_score)
        else:
            db.set_progress(lesson_key, "in_progress", min(99, max(1, int(current.get("percent") or 0))), best_score)

    return {"score": score, "max_score": max_score, "percent": percent, "passed": passed, "pass_score": pass_score, "details": details}


def _answer_rows(attempt_id: int) -> dict[str, dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM exam_answers WHERE attempt_id=? ORDER BY id", (attempt_id,)).fetchall()
    result = {}
    for row in rows:
        item = dict(row)
        item["answer"] = json.loads(item.pop("answer_json"))
        item["feedback"] = json.loads(item.pop("feedback_json"))
        result[item["question_id"]] = item
    return result


def _attempt_title(attempt: dict[str, Any], lang: str) -> str:
    if attempt.get("title_en") or attempt.get("title_zh"):
        return attempt["title_en"] if lang == "en" else attempt["title_zh"]
    lesson = LESSON_MAP.get(attempt["lesson_key"])
    return title_for(lesson, lang) if lesson else attempt["lesson_key"]


def _submitted_attempts(limit: int = 100) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT a.*,m.mode,m.scope_key,m.title_zh,m.title_en
               FROM exam_attempts a LEFT JOIN exam_v2_meta m ON m.attempt_id=a.id
               WHERE a.status='submitted' ORDER BY a.id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def _history_stats(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        return {"count": 0, "passed": 0, "pass_rate": 0.0, "average": 0.0, "best": 0.0}
    passed = sum(1 for x in items if x.get("passed"))
    percents = [float(x.get("percent") or 0) for x in items]
    return {"count": len(items), "passed": passed, "pass_rate": round(passed / len(items) * 100, 1),
            "average": round(sum(percents) / len(percents), 1), "best": round(max(percents), 1)}


def _latest_question_state() -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT ea.*,a.submitted_at FROM exam_answers ea
               JOIN exam_attempts a ON a.id=ea.attempt_id
               WHERE a.status='submitted' ORDER BY ea.id DESC"""
        ).fetchall()
    latest: dict[str, dict[str, Any]] = {}
    wrong_counts: dict[str, int] = {}
    for row in rows:
        item = dict(row)
        if not item["correct"]:
            wrong_counts[item["question_id"]] = wrong_counts.get(item["question_id"], 0) + 1
        latest.setdefault(item["question_id"], item)

    unresolved = []
    for qid, item in latest.items():
        if item["correct"]:
            continue
        indexed = QUESTION_INDEX.get(qid)
        if not indexed:
            continue
        lesson_key, q = indexed
        unresolved.append({**item, "lesson_key": lesson_key, "question": q, "wrong_count": wrong_counts.get(qid, 1),
                           "difficulty": difficulty_for(q), "knowledge": knowledge_for(lesson_key, q)})
    unresolved.sort(key=lambda x: x["id"], reverse=True)
    return unresolved


@router.get("/exam-lab", response_class=HTMLResponse)
def exam_lab(request: Request):
    lang = _lang(request)
    submitted = _submitted_attempts(1000)
    weekly_items = []
    for lesson in LESSONS:
        bank = bank_for(lesson.key)
        latest = next((x for x in submitted if x.get("mode") == "weekly" and x.get("scope_key") == lesson.key), None)
        best_values = [float(x.get("percent") or 0) for x in submitted if x.get("mode") == "weekly" and x.get("scope_key") == lesson.key]
        weekly_items.append({"lesson": lesson, "title": title_for(lesson, lang), "bank_count": len(bank), "latest": latest,
                             "best": max(best_values) if best_values else None, "pass_score": EXAMS[lesson.key].pass_score})
    c = _nav(request, lang)
    c.update({"weekly_items": weekly_items, "stats": _history_stats(submitted),
              "mistake_count": len(_latest_question_state()), "stage_count": len(STAGES)})
    return templates.TemplateResponse(request=request, name="exam_lab.html", context=c)


@router.post("/exams/{lesson_key}/random-start")
def start_random_weekly(request: Request, lesson_key: str):
    if lesson_key not in EXAMS:
        raise HTTPException(404)
    lang = _lang(request)
    lesson = LESSON_MAP[lesson_key]
    seed = secrets.randbits(31)
    pool = [(lesson_key, q) for q in bank_for(lesson_key)]
    target = 8 if lesson_key == "week00" else min(6, len(pool))
    selected = _choose_balanced(pool, target, seed)
    attempt_id = _create_attempt(lesson_key=lesson_key, lang=lang, mode="weekly", scope_key=lesson_key,
                                 title_zh=f"Week {lesson.week} 随机周测", title_en=f"Week {lesson.week} Randomized Exam",
                                 selected=selected, pass_score=EXAMS[lesson_key].pass_score, seed=seed)
    return RedirectResponse(f"/exam-v2/attempt/{attempt_id}", status_code=303)


@router.get("/stage-exams", response_class=HTMLResponse)
def stage_exams(request: Request):
    lang = _lang(request)
    submitted = _submitted_attempts(1000)
    items = []
    for stage in STAGES:
        rows = [x for x in submitted if x.get("mode") == "stage" and x.get("scope_key") == stage.key]
        items.append({"stage": stage, "title": stage.en if lang == "en" else stage.zh, "attempt_count": len(rows),
                      "latest": rows[0] if rows else None,
                      "best": max((float(x.get("percent") or 0) for x in rows), default=None),
                      "weeks_text": ", ".join(w.replace("week", "W") for w in stage.weeks)})
    c = _nav(request, lang)
    c["stage_items"] = items
    return templates.TemplateResponse(request=request, name="stage_exams.html", context=c)


@router.post("/stage-exams/{stage_key}/start")
def start_stage_exam(request: Request, stage_key: str):
    stage = STAGE_MAP.get(stage_key)
    if not stage:
        raise HTTPException(404)
    lang = _lang(request)
    seed = secrets.randbits(31)
    selected = _choose_stage(stage, seed)
    attempt_id = _create_attempt(lesson_key=stage.key, lang=lang, mode="stage", scope_key=stage.key,
                                 title_zh=stage.zh, title_en=stage.en, selected=selected,
                                 pass_score=stage.pass_score, seed=seed)
    return RedirectResponse(f"/exam-v2/attempt/{attempt_id}", status_code=303)


@router.get("/mistakes", response_class=HTMLResponse)
def mistakes(request: Request):
    lang = _lang(request)
    rows = _latest_question_state()
    items = []
    for item in rows:
        q: Question = item["question"]
        items.append({**item, "prompt": q.en if lang == "en" else q.zh, "correct_answer": correct_text(q, lang),
                      "lesson_title": title_for(LESSON_MAP[item["lesson_key"]], lang)})
    c = _nav(request, lang)
    c["mistakes"] = items
    return templates.TemplateResponse(request=request, name="mistakes.html", context=c)


@router.post("/mistakes/start")
def start_mistake_practice(request: Request):
    lang = _lang(request)
    rows = _latest_question_state()[:10]
    if not rows:
        return RedirectResponse("/mistakes", status_code=303)
    seed = secrets.randbits(31)
    selected = [(x["lesson_key"], x["question"]) for x in rows]
    attempt_id = _create_attempt(lesson_key="mistakes", lang=lang, mode="mistakes", scope_key="mistakes",
                                 title_zh="错题专项复习", title_en="Mistake Review Practice",
                                 selected=selected, pass_score=80, seed=seed)
    return RedirectResponse(f"/exam-v2/attempt/{attempt_id}", status_code=303)


@router.get("/exam-history", response_class=HTMLResponse)
def exam_history(request: Request):
    lang = _lang(request)
    items = _submitted_attempts(100)
    for item in items:
        item["display_title"] = _attempt_title(item, lang)
    trend = list(reversed(items[:20]))
    c = _nav(request, lang)
    c.update({"history": items, "stats": _history_stats(items), "trend": trend})
    return templates.TemplateResponse(request=request, name="exam_history.html", context=c)


@router.get("/question-bank", response_class=HTMLResponse)
def question_bank(request: Request):
    lang = _lang(request)
    items = []
    for lesson in LESSONS:
        bank = bank_for(lesson.key)
        counts = {"easy": 0, "medium": 0, "hard": 0}
        kinds: dict[str, int] = {}
        for q in bank:
            counts[difficulty_for(q)] += 1
            kinds[q.kind] = kinds.get(q.kind, 0) + 1
        items.append({"lesson": lesson, "title": title_for(lesson, lang), "count": len(bank),
                      "difficulty": counts, "kinds": kinds, "knowledge": WEEK_TAGS.get(lesson.key, ())})
    c = _nav(request, lang)
    c["bank_items"] = items
    return templates.TemplateResponse(request=request, name="question_bank.html", context=c)


@router.get("/exam-results/{attempt_id}")
def compatible_result(attempt_id: int):
    attempt = _attempt(attempt_id)
    if not attempt:
        raise HTTPException(404)
    if attempt.get("mode"):
        return RedirectResponse(f"/exam-v2/attempt/{attempt_id}/result", status_code=303)
    return RedirectResponse(f"/exams/attempt/{attempt_id}/result", status_code=303)


@router.get("/exam-v2/attempt/{attempt_id}", response_class=HTMLResponse)
def take_v2_exam(request: Request, attempt_id: int):
    attempt = _attempt(attempt_id)
    if not attempt or not attempt.get("mode"):
        raise HTTPException(404)
    if attempt["status"] == "submitted":
        return RedirectResponse(f"/exam-v2/attempt/{attempt_id}/result", status_code=303)
    lang = normalize_lang(attempt["language"])
    selected = _selected_questions(attempt_id)
    c = _nav(request, lang)
    c.update({"attempt": attempt, "exam_title": _attempt_title(attempt, lang),
              "questions": [_question_view(x, lang) for x in selected]})
    return templates.TemplateResponse(request=request, name="exam_v2_attempt.html", context=c)


@router.post("/exam-v2/attempt/{attempt_id}/submit")
async def submit_v2_exam(request: Request, attempt_id: int):
    attempt = _attempt(attempt_id)
    if not attempt or not attempt.get("mode"):
        raise HTTPException(404)
    if attempt["status"] == "submitted":
        return RedirectResponse(f"/exam-v2/attempt/{attempt_id}/result", status_code=303)
    selected = _selected_questions(attempt_id)
    form = await request.form()
    answers: dict[str, Any] = {}
    for item in selected:
        q: Question = item["question"]
        name = f"q_{q.id}"
        answers[q.id] = list(form.getlist(name)) if q.kind == "multiple" else str(form.get(name, ""))
    _save_submission(attempt, answers, selected)
    return RedirectResponse(f"/exam-v2/attempt/{attempt_id}/result", status_code=303)


@router.get("/exam-v2/attempt/{attempt_id}/result", response_class=HTMLResponse)
def v2_result(request: Request, attempt_id: int):
    attempt = _attempt(attempt_id)
    if not attempt or not attempt.get("mode"):
        raise HTTPException(404)
    if attempt["status"] != "submitted":
        return RedirectResponse(f"/exam-v2/attempt/{attempt_id}", status_code=303)
    lang = normalize_lang(attempt["language"])
    selected = _selected_questions(attempt_id)
    answers = _answer_rows(attempt_id)
    details = []
    for item in selected:
        q: Question = item["question"]
        saved = answers.get(q.id, {})
        details.append({"seq": item["seq"], "prompt": q.en if lang == "en" else q.zh,
                        "answer": _display_answer(saved.get("answer")), "correct_answer": correct_text(q, lang),
                        "earned": float(saved.get("earned") or 0), "max_points": float(saved.get("max_points") or q.points),
                        "correct": bool(saved.get("correct")), "feedback": saved.get("feedback") or {},
                        "difficulty": item["difficulty"], "knowledge": item["knowledge"]})
    c = _nav(request, lang)
    c.update({"attempt": attempt, "exam_title": _attempt_title(attempt, lang), "details": details, "mode": attempt["mode"]})
    return templates.TemplateResponse(request=request, name="exam_v2_result.html", context=c)

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .course import LESSONS, LESSON_MAP, title_for
from .db import Database, now_iso
from .i18n import normalize_lang, tr

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
DATA_DIR = Path(os.getenv("LLM_LEARNING_DATA_DIR", str(REPO_ROOT / "data")))
DB_PATH = DATA_DIR / "learning.db"
PASS_SCORE = 80

templates = Jinja2Templates(directory=APP_DIR / "templates")
db = Database(DB_PATH)
router = APIRouter()


@dataclass(frozen=True)
class Question:
    id: str
    kind: str
    points: float
    zh: str
    en: str
    options: tuple[tuple[str, str, str], ...] = ()
    answer: Any = None
    accepted: tuple[str, ...] = ()
    concepts: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class Exam:
    lesson_key: str
    zh: str
    en: str
    questions: tuple[Question, ...]
    pass_score: int = PASS_SCORE

    @property
    def max_score(self) -> float:
        return sum(q.points for q in self.questions)


def o(value: str, zh: str, en: str):
    return value, zh, en


def single(qid, zh, en, options, answer, points=20):
    return Question(qid, "single", points, zh, en, tuple(options), answer=answer)


def multiple(qid, zh, en, options, answer, points=20):
    return Question(qid, "multiple", points, zh, en, tuple(options), answer=tuple(answer))


def boolean(qid, zh, en, answer, points=20):
    return Question(qid, "boolean", points, zh, en, answer=bool(answer))


def fill(qid, zh, en, accepted, points=20):
    return Question(qid, "fill", points, zh, en, accepted=tuple(accepted))


def short(qid, zh, en, concepts, points=20):
    return Question(qid, "short", points, zh, en, concepts=tuple(tuple(x) for x in concepts))


EXAMS: dict[str, Exam] = {
    "week00": Exam("week00", "Week 0 基线能力测试", "Week 0 Baseline Assessment", (
        single("w00q1", "Token 最准确的描述是什么？", "Which best describes a token?", (
            o("a", "固定等于一个字符", "Always one character"), o("b", "Tokenizer 切分后的模型输入单位", "A model input unit produced by tokenization"),
            o("c", "向量数据库的一行", "A vector DB row"), o("d", "GPU 线程", "A GPU thread")), "b", 10),
        single("w00q2", "Embedding 的主要用途是什么？", "What is the main purpose of embeddings?", (
            o("a", "将对象表示成可计算的向量", "Represent objects as computable vectors"), o("b", "压缩 Docker 镜像", "Compress Docker images"),
            o("c", "替代数据库事务", "Replace DB transactions"), o("d", "执行 Shell", "Execute shell")), "a", 10),
        multiple("w00q3", "哪些属于常见 LLM 解码控制参数？", "Which are common LLM decoding controls?", (
            o("temperature", "Temperature", "Temperature"), o("top_p", "Top-P", "Top-P"), o("batch", "数据库 Batch", "Database batch"), o("stop", "Stop Sequence", "Stop sequence")), ("temperature", "top_p", "stop"), 10),
        boolean("w00q4", "RAG 可以保证模型永远不产生幻觉。", "RAG guarantees zero hallucination.", False, 10),
        fill("w00q5", "Query 与 Key 相关性常通过什么核心操作计算？", "What core operation commonly measures Query-Key relevance?", ("dot product", "点积", "scaled dot product"), 10),
        single("w00q6", "Tool Calling 中真正执行工具的是谁？", "Who actually executes a tool call?", (
            o("a", "模型权重", "Model weights"), o("b", "应用程序/工具运行时", "Application/tool runtime"), o("c", "Tokenizer", "Tokenizer"), o("d", "向量数据库", "Vector DB")), "b", 10),
        boolean("w00q7", "没有最大步骤限制的 Agent Loop 存在死循环风险。", "An unbounded agent loop can enter an infinite loop.", True, 10),
        single("w00q8", "MCP 的核心目标更接近哪项？", "Which best describes MCP's core goal?", (
            o("a", "统一训练算法", "Standardize training algorithms"), o("b", "标准化 AI 应用与工具/资源的连接", "Standardize AI app connections to tools/resources"),
            o("c", "替代 HTTP", "Replace HTTP"), o("d", "只用于图片", "Only for images")), "b", 10),
        short("w00q9", "简述 Prompt、RAG、Fine-tuning 分别主要解决什么问题。", "Explain what Prompting, RAG, and Fine-tuning mainly solve.", (
            ("prompt", "instruction", "指令", "约束"), ("rag", "retrieval", "检索", "外部知识"), ("fine-tuning", "finetuning", "微调", "行为适配", "能力适配")), 10),
        short("w00q10", "列出至少三个生产 Agent 的工程约束。", "Name at least three production-agent engineering controls.", (
            ("max steps", "步骤限制", "最大步骤"), ("timeout", "超时"), ("budget", "预算", "成本"), ("permission", "approval", "权限", "审批"), ("retry", "circuit breaker", "重试", "熔断")), 10),
    ), 70),
    "week01": Exam("week01", "Week 1 数学与机器学习基础周测", "Week 1 Math & ML Foundations Exam", (
        single("w01q1", "Cosine Similarity 主要衡量什么？", "What does cosine similarity mainly measure?", (
            o("a", "向量方向相似程度", "Similarity of vector direction"), o("b", "文件大小", "File size"), o("c", "Epoch 数", "Epoch count"), o("d", "GPU 温度", "GPU temperature")), "a", 15),
        multiple("w01q2", "Learning Rate 过大可能导致哪些现象？", "What can an overly large learning rate cause?", (
            o("oscillate", "Loss 震荡", "Loss oscillation"), o("diverge", "训练发散", "Divergence"), o("stable", "一定更稳定", "Always more stable"), o("nan", "NaN/Inf", "NaN/Inf")), ("oscillate", "diverge", "nan"), 15),
        boolean("w01q3", "改变 Batch Size 会改变模型参数数量。", "Changing batch size changes model parameter count.", False, 15),
        fill("w01q4", "训练集很好而验证集持续恶化通常称为什么？", "What is it called when training improves while validation degrades?", ("overfitting", "过拟合"), 15),
        short("w01q5", "解释训练集、验证集、测试集的职责。", "Explain the roles of train, validation, and test sets.", (
            ("training", "train", "训练", "拟合参数"), ("validation", "valid", "验证", "调参", "模型选择"), ("test", "测试", "最终评估", "泛化")), 20),
        short("w01q6", "为什么梯度下降需要合适的 Learning Rate？", "Why does gradient descent need an appropriate learning rate?", (
            ("step", "步长", "更新幅度"), ("large", "过大", "diverge", "发散"), ("small", "过小", "slow", "收敛慢")), 20),
    ), 80),
    "week02": Exam("week02", "Week 2 神经网络与 PyTorch 周测", "Week 2 Neural Networks & PyTorch Exam", (
        single("w02q1", "为什么需要非线性激活函数？", "Why are nonlinear activations needed?", (
            o("a", "否则多层线性层仍等价于线性变换", "Without them stacked linear layers remain a linear transform"), o("b", "为了增大文件", "To enlarge files"),
            o("c", "替代 Loss", "Replace loss"), o("d", "只为 GPU", "Only for GPU")), "a", 15),
        boolean("w02q2", "PyTorch 默认会累积梯度。", "PyTorch accumulates gradients by default.", True, 15),
        single("w02q3", "推理时使用 model.eval() 和 torch.no_grad() 的主要原因是什么？", "Why use model.eval() and torch.no_grad() for inference?", (
            o("a", "切换推理行为并避免不必要梯度图", "Use inference behavior and avoid unnecessary gradient graphs"), o("b", "重新训练", "Retrain"), o("c", "增加参数", "Increase parameters"), o("d", "修改标签", "Modify labels")), "a", 15),
        fill("w02q4", "PyTorch 常用什么对象保存模型参数字典？", "What common PyTorch object stores model parameter dictionaries?", ("state_dict", "state dict", "state_dict()"), 15),
        short("w02q5", "描述标准训练迭代顺序。", "Describe a standard training iteration.", (
            ("forward", "前向"), ("loss", "损失"), ("backward", "反向", "梯度"), ("optimizer", "step", "更新参数"), ("zero_grad", "清零梯度")), 20),
        short("w02q6", "列出至少三类常见 Tensor 错误。", "Name at least three common tensor error categories.", (
            ("shape", "维度", "尺寸"), ("dtype", "类型"), ("device", "cpu", "gpu", "设备"), ("nan", "inf")), 20),
    ), 80),
}

# Week 3-18 use a compact true/false checkpoint bank in V1. The engine already supports richer formats.
_TF: dict[str, tuple[tuple[str, str, bool], ...]] = {
    "week03": (("BPE 会通过合并高频符号对形成子词。", "BPE can form subwords by merging frequent symbol pairs.", True), ("字符数一定等于 Token 数。", "Character count always equals token count.", False), ("Temperature 会影响采样随机性。", "Temperature affects sampling randomness.", True), ("Context Window 与单次推理可处理的上下文范围有关。", "Context window concerns how much context one inference can process.", True)),
    "week04": (("QKᵀ 用于计算 Query 与 Key 的相关性分数。", "QK^T computes Query-Key relevance scores.", True), ("Causal Mask 用于阻止看到未来 Token。", "A causal mask blocks future tokens.", True), ("Multi-Head Attention 只能学习一种关系。", "Multi-head attention can learn only one relation.", False), ("Attention 天然包含绝对位置信息，因此不需要任何位置机制。", "Attention inherently contains absolute position, so no position mechanism is needed.", False)),
    "week05": (("System Prompt 常用于设定角色和高优先级规则。", "System prompts often set roles and high-priority rules.", True), ("生产 LLM API 不需要 Timeout。", "Production LLM APIs do not need timeouts.", False), ("Streaming 可降低感知等待。", "Streaming can reduce perceived waiting time.", True), ("Few-shot 表示提供少量示例。", "Few-shot means providing a few examples.", True)),
    "week06": (("Structured Output 的目标之一是让输出满足可验证结构。", "Structured output aims for verifiable output structure.", True), ("Tool Calling 中工具通常由应用运行时执行。", "Tools are usually executed by the application runtime.", True), ("Pydantic 可用于数据模型与校验。", "Pydantic can model and validate data.", True), ("工具参数非法时应绕过 Schema 直接执行。", "Invalid tool arguments should bypass schema validation.", False)),
    "week07": (("Embedding 通常把文本映射为高维向量。", "Embeddings map text to high-dimensional vectors.", True), ("Top-K 返回排名最高的 K 个候选。", "Top-K returns the K highest-ranked candidates.", True), ("Metadata Filter 可先缩小候选范围。", "Metadata filters can narrow the candidate scope.", True), ("FAISS 是关系数据库事务引擎。", "FAISS is a relational transaction engine.", False)),
    "week08": (("Retriever 用于从知识源找到相关上下文。", "A retriever finds relevant context from knowledge sources.", True), ("Chunk Size 不会影响 RAG 质量。", "Chunk size cannot affect RAG quality.", False), ("保留 source/chunk_id/score 有利于调试和追溯。", "Keeping source/chunk_id/score helps debugging and traceability.", True), ("证据不足时的 no-answer 策略可降低强行编造。", "A no-answer strategy can reduce forced fabrication when evidence is insufficient.", True)),
    "week09": (("Hybrid Search 常组合稠密向量与稀疏关键词检索。", "Hybrid search often combines dense and sparse retrieval.", True), ("Reranker 用于对候选进行更精细排序。", "A reranker reorders candidates more precisely.", True), ("Query Rewrite 可让查询更适合检索。", "Query rewriting can make queries retrieval-friendly.", True), ("Parent Document Retrieval 不能提供更大上下文。", "Parent-document retrieval cannot provide larger context.", False)),
    "week10": (("Faithfulness 衡量答案是否忠于上下文证据。", "Faithfulness measures grounding in context evidence.", True), ("RAG 评测只看最终答案即可。", "RAG evaluation only needs final answers.", False), ("固定 Eval Dataset 有利于回归比较。", "A fixed eval dataset helps regression comparison.", True), ("Retrieval Recall 关注相关证据是否被找回。", "Retrieval recall concerns whether relevant evidence was retrieved.", True)),
    "week11": (("Agent 可循环选择动作/工具并观察结果。", "An agent can loop through actions/tools and observations.", True), ("Observation 通常是工具执行结果。", "An observation is usually a tool result.", True), ("ReAct 强调 Reasoning 与 Acting。", "ReAct combines reasoning and acting.", True), ("Agent 与一次性 Chat 完全没有区别。", "Agents are identical to one-shot chat.", False)),
    "week12": (("Max Steps 可限制无界循环。", "Max steps can limit unbounded loops.", True), ("生产 Agent 应默认允许所有危险 Shell 命令。", "Production agents should allow all dangerous shell commands by default.", False), ("No Progress Detection 用于识别没有实质推进的循环。", "No-progress detection identifies loops without meaningful progress.", True), ("高风险删除/生产写入适合 Human Approval。", "High-risk deletion/production writes are good candidates for human approval.", True)),
    "week13": (("MCP Server 可暴露 Tools、Resources、Prompts。", "An MCP server can expose tools, resources, and prompts.", True), ("MCP 标准化 AI 应用与外部能力连接。", "MCP standardizes AI-app connections to external capabilities.", True), ("stdio 可以是 MCP Transport。", "stdio can be an MCP transport.", True), ("MCP 与 Tool Calling 完全相同。", "MCP and tool calling are identical.", False)),
    "week14": (("LLM Gateway 可统一多个 Provider 的访问治理。", "An LLM gateway can unify provider access and governance.", True), ("Fallback 可在主模型失败时使用备用模型。", "Fallback can use a backup model when the primary fails.", True), ("逻辑模型名可降低业务与具体 Provider 的耦合。", "Logical model names can reduce provider coupling.", True), ("Model Router 不应考虑成本、延迟或隐私。", "A model router should not consider cost, latency, or privacy.", False)),
    "week15": (("Trace 可帮助重建模型/工具执行路径。", "Traces can reconstruct model/tool execution paths.", True), ("Prompt Injection 只可能来自用户输入。", "Prompt injection can only come from user input.", False), ("Regression Test 可发现版本变化导致的能力退化。", "Regression tests can detect capability degradation after changes.", True), ("工具权限应遵循最小权限原则。", "Tool permissions should follow least privilege.", True)),
    "week16": (("TTFT 表示 Time To First Token。", "TTFT means Time To First Token.", True), ("更长上下文通常增加 KV Cache 内存开销。", "Longer context generally increases KV-cache memory use.", True), ("GGUF 常见于 llama.cpp 本地量化模型场景。", "GGUF is common in llama.cpp local quantized deployments.", True), ("vLLM 不适合模型推理服务。", "vLLM is not suitable for model serving.", False)),
    "week17": (("LoRA 使用低秩适配训练少量新增参数。", "LoRA trains a small number of low-rank adapter parameters.", True), ("所有知识更新问题都应优先 Fine-tuning。", "All knowledge updates should prioritize fine-tuning.", False), ("最新私有文档知识通常可优先考虑 RAG。", "RAG is often a first choice for current private-document knowledge.", True), ("SFT 表示 Supervised Fine-Tuning。", "SFT means Supervised Fine-Tuning.", True)),
    "week18": (("Coding Agent 需要代码搜索以定位相关代码。", "Coding agents need code search to locate relevant code.", True), ("代码修改后应尽量通过构建/测试验证。", "Code changes should be validated with builds/tests when possible.", True), ("git diff 有助于审查实际改动范围。", "git diff helps inspect the actual scope of changes.", True), ("合理 Coding Agent 应修改后直接发布，不需要测试。", "A sound coding agent should deploy immediately after edits without tests.", False)),
}
for key, rows in _TF.items():
    qs = tuple(boolean(f"{key}q{i}", zh, en, ans, 25) for i, (zh, en, ans) in enumerate(rows, 1))
    EXAMS[key] = Exam(key, f"{key.replace('week', 'Week ')} 基础周测", f"{key.replace('week', 'Week ')} Checkpoint Exam", qs, 80)


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def local_exam(exam: Exam, lang: str) -> dict[str, Any]:
    en = lang == "en"
    return {"title": exam.en if en else exam.zh, "pass_score": exam.pass_score, "max_score": exam.max_score, "questions": [
        {"id": q.id, "type": q.kind, "points": q.points, "prompt": q.en if en else q.zh,
         "options": [{"value": v, "label": e if en else z} for v, z, e in q.options]} for q in exam.questions]}


def grade_question(q: Question, answer: Any) -> dict[str, Any]:
    matched: list[str] = []
    missing: list[str] = []
    if q.kind == "single":
        earned = q.points if str(answer or "") == str(q.answer) else 0
    elif q.kind == "multiple":
        earned = q.points if set(answer or []) == set(q.answer or []) else 0
    elif q.kind == "boolean":
        value = _norm(str(answer or ""))
        actual = value in {"true", "1", "yes", "是", "正确"}
        earned = q.points if value and actual is q.answer else 0
    elif q.kind == "fill":
        value = _norm(str(answer or ""))
        earned = q.points if any(value == _norm(x) for x in q.accepted) else 0
    else:
        value = _norm(str(answer or ""))
        for group in q.concepts:
            (matched if any(_norm(term) in value for term in group) else missing).append(group[0])
        earned = round(q.points * len(matched) / len(q.concepts), 2) if q.concepts else 0
    return {"question_id": q.id, "earned": float(earned), "max_points": q.points, "correct": float(earned) == q.points, "matched": matched, "missing": missing}


def grade_exam(exam: Exam, answers: dict[str, Any]) -> dict[str, Any]:
    details = [grade_question(q, answers.get(q.id)) for q in exam.questions]
    score = round(sum(x["earned"] for x in details), 2)
    percent = round(score / exam.max_score * 100, 2) if exam.max_score else 0
    return {"score": score, "max_score": exam.max_score, "percent": percent, "passed": percent >= exam.pass_score, "pass_score": exam.pass_score, "details": details}


def correct_text(q: Question, lang: str) -> str:
    en = lang == "en"
    if q.kind in {"single", "multiple"}:
        wanted = {str(q.answer)} if q.kind == "single" else set(q.answer or [])
        return ", ".join(e if en else z for v, z, e in q.options if v in wanted)
    if q.kind == "boolean":
        return ("True" if q.answer else "False") if en else ("正确" if q.answer else "错误")
    if q.kind == "fill":
        return " / ".join(q.accepted)
    return ", ".join(group[0] for group in q.concepts)


def init_tables() -> None:
    with db.connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS exam_attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_key TEXT NOT NULL, language TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'started', started_at TEXT NOT NULL, submitted_at TEXT,
            score REAL, max_score REAL, percent REAL, passed INTEGER, pass_score REAL);
        CREATE TABLE IF NOT EXISTS exam_answers(
            id INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id INTEGER NOT NULL, question_id TEXT NOT NULL,
            answer_json TEXT NOT NULL, earned REAL NOT NULL, max_points REAL NOT NULL, correct INTEGER NOT NULL,
            feedback_json TEXT NOT NULL DEFAULT '{}', FOREIGN KEY(attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE);
        CREATE INDEX IF NOT EXISTS idx_exam_attempt_lesson ON exam_attempts(lesson_key,id DESC);
        CREATE INDEX IF NOT EXISTS idx_exam_answer_attempt ON exam_answers(attempt_id);
        """)


init_tables()


def _lang(request: Request) -> str:
    return normalize_lang(request.query_params.get("lang") or request.cookies.get("lang"))


def _nav(request: Request, lang: str) -> dict[str, Any]:
    progress = db.all_progress()
    lessons = [{"key": l.key, "week": l.week, "title": title_for(l, lang), "progress": progress.get(l.key, {"status": "not_started", "percent": 0, "score": None})} for l in LESSONS]
    return {"request": request, "lang": lang, "t": lambda key: tr(lang, key), "lessons": lessons, "current_path": request.url.path}


def _attempt(attempt_id: int) -> dict[str, Any] | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM exam_attempts WHERE id=?", (attempt_id,)).fetchone()
    return dict(row) if row else None


def attempts(lesson_key: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    with db.connect() as conn:
        if lesson_key:
            rows = conn.execute("SELECT * FROM exam_attempts WHERE lesson_key=? ORDER BY id DESC LIMIT ?", (lesson_key, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM exam_attempts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(x) for x in rows]


def exam_summary(lesson_key: str) -> dict[str, Any] | None:
    exam = EXAMS.get(lesson_key)
    if not exam:
        return None
    submitted = [x for x in attempts(lesson_key, 1000) if x["status"] == "submitted"]
    latest = submitted[0] if submitted else None
    best = max(submitted, key=lambda x: x["percent"] or 0) if submitted else None
    return {"pass_score": exam.pass_score, "question_count": len(exam.questions), "latest": latest, "best": best, "attempt_count": len(submitted)}


def _save_result(attempt: dict[str, Any], answers: dict[str, Any], result: dict[str, Any]) -> None:
    with db.connect() as conn:
        conn.execute("UPDATE exam_attempts SET status='submitted',submitted_at=?,score=?,max_score=?,percent=?,passed=?,pass_score=? WHERE id=?",
                     (now_iso(), result["score"], result["max_score"], result["percent"], 1 if result["passed"] else 0, result["pass_score"], attempt["id"]))
        for detail in result["details"]:
            conn.execute("INSERT INTO exam_answers(attempt_id,question_id,answer_json,earned,max_points,correct,feedback_json) VALUES(?,?,?,?,?,?,?)",
                         (attempt["id"], detail["question_id"], json.dumps(answers.get(detail["question_id"]), ensure_ascii=False), detail["earned"], detail["max_points"], 1 if detail["correct"] else 0,
                          json.dumps({"matched": detail["matched"], "missing": detail["missing"]}, ensure_ascii=False)))
    current = db.all_progress().get(attempt["lesson_key"], {"percent": 0, "status": "not_started", "score": None})
    best_score = max(float(current["score"] or 0), float(result["percent"]))
    if result["passed"]:
        db.set_progress(attempt["lesson_key"], "completed", 100, best_score)
    else:
        db.set_progress(attempt["lesson_key"], "in_progress", min(99, max(1, int(current["percent"] or 0))), best_score)


def _result(attempt_id: int) -> dict[str, Any] | None:
    attempt = _attempt(attempt_id)
    if not attempt:
        return None
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM exam_answers WHERE attempt_id=? ORDER BY id", (attempt_id,)).fetchall()
    answer_rows = []
    for row in rows:
        item = dict(row)
        item["answer"] = json.loads(item.pop("answer_json"))
        item["feedback"] = json.loads(item.pop("feedback_json"))
        answer_rows.append(item)
    attempt["answers"] = answer_rows
    return attempt


@router.get("/exams", response_class=HTMLResponse)
def exam_center(request: Request):
    lang = _lang(request)
    items = []
    for lesson in LESSONS:
        exam = EXAMS.get(lesson.key)
        if exam:
            items.append({"lesson": lesson, "lesson_title": title_for(lesson, lang), "exam": local_exam(exam, lang), "summary": exam_summary(lesson.key)})
    c = _nav(request, lang); c["exam_items"] = items
    return templates.TemplateResponse(request=request, name="exams.html", context=c)


@router.post("/exams/{lesson_key}/start")
def start_exam(request: Request, lesson_key: str):
    if lesson_key not in EXAMS:
        raise HTTPException(404)
    with db.connect() as conn:
        cur = conn.execute("INSERT INTO exam_attempts(lesson_key,language,status,started_at) VALUES(?,?,?,?)", (lesson_key, _lang(request), "started", now_iso()))
        attempt_id = int(cur.lastrowid)
    return RedirectResponse(f"/exams/attempt/{attempt_id}", status_code=303)


@router.get("/exams/attempt/{attempt_id}", response_class=HTMLResponse)
def take_exam(request: Request, attempt_id: int):
    attempt = _attempt(attempt_id)
    if not attempt:
        raise HTTPException(404)
    if attempt["status"] == "submitted":
        return RedirectResponse(f"/exams/attempt/{attempt_id}/result", status_code=303)
    exam = EXAMS.get(attempt["lesson_key"])
    lang = normalize_lang(attempt["language"])
    c = _nav(request, lang); c.update({"attempt": attempt, "exam_view": local_exam(exam, lang)})
    return templates.TemplateResponse(request=request, name="exam_attempt.html", context=c)


@router.post("/exams/attempt/{attempt_id}/submit")
async def submit_exam(request: Request, attempt_id: int):
    attempt = _attempt(attempt_id)
    if not attempt:
        raise HTTPException(404)
    if attempt["status"] == "submitted":
        return RedirectResponse(f"/exams/attempt/{attempt_id}/result", status_code=303)
    exam = EXAMS[attempt["lesson_key"]]
    form = await request.form()
    answers: dict[str, Any] = {}
    for q in exam.questions:
        name = f"q_{q.id}"
        answers[q.id] = list(form.getlist(name)) if q.kind == "multiple" else str(form.get(name, ""))
    result = grade_exam(exam, answers)
    _save_result(attempt, answers, result)
    return RedirectResponse(f"/exams/attempt/{attempt_id}/result", status_code=303)


@router.get("/exams/attempt/{attempt_id}/result", response_class=HTMLResponse)
def score_report(request: Request, attempt_id: int):
    result = _result(attempt_id)
    if not result:
        raise HTTPException(404)
    if result["status"] != "submitted":
        return RedirectResponse(f"/exams/attempt/{attempt_id}", status_code=303)
    exam = EXAMS[result["lesson_key"]]
    lang = normalize_lang(result["language"])
    qmap = {q.id: q for q in exam.questions}
    details = []
    for item in result["answers"]:
        q = qmap[item["question_id"]]
        details.append({**item, "prompt": q.en if lang == "en" else q.zh, "correct_answer": correct_text(q, lang)})
    c = _nav(request, lang); c.update({"result": result, "details": details, "exam_view": local_exam(exam, lang), "lesson": LESSON_MAP[result["lesson_key"]]})
    return templates.TemplateResponse(request=request, name="exam_result.html", context=c)

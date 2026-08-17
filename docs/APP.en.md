# Local Learning App

This repository includes a local-first learning and examination app in addition to the Markdown curriculum.

## Features

- Chinese / English course switching with shared progress.
- Reading progress tracking; manual reading progress is capped below 100%.
- A dedicated Exam Center: start an attempt, answer questions, submit, system-grade, view reports, and retake.
- Course scores **cannot be entered manually**. Only the exam engine can write a score.
- Passing the configured exam automatically marks the lesson 100% / completed; failing keeps it in progress.
- Single-choice, multiple-choice, true/false, and fill-in questions use deterministic automatic grading.
- Short answers receive partial credit against explicit concept rubrics, with matched and missing concepts shown in the report.
- Randomized weekly papers with difficulty balancing and a stored paper snapshot per attempt.
- Question metadata for Easy / Medium / Hard difficulty and knowledge tags.
- Mistake Book showing only questions whose latest recorded answer is still incorrect.
- One-click mistake-review practice generated from unresolved mistakes.
- Score analytics including attempt count, average, best score, pass rate, and recent trend.
- Five cross-week Stage Exams covering the full 18-week curriculum.
- Question Bank overview with counts by type, difficulty, and knowledge coverage.
- Markdown thoughts linked to lessons with tags.
- External resource library for papers, tutorials, videos, blogs, and GitHub projects.
- Local SQLite storage with no external database.
- JSON backup includes progress, thoughts, resources, exam history, answer details, and randomized-paper snapshots.
- Direct Python startup plus Docker / Docker Compose.

## V2 Exam Flow

```text
Study lesson
  ↓
Exam Center / lesson exam card
  ↓
Random selection + difficulty balancing
  ↓
Persist this attempt's paper snapshot
  ↓
Answer questions
  ↓
Submit
  ↓
Automatic system grading
  ↓
Score report + per-question feedback + concept feedback
  ↓
Pass → lesson 100% / completed
Fail → lesson stays in progress; retake allowed
```

Weeks 0–2 retain the original mixed-format banks. Weeks 3–18 now add single-choice, multiple-choice, and short-answer questions on top of the original checkpoints, giving randomized weekly exams Easy / Medium / Hard coverage. The bank can keep growing without breaking historical reports because every V2 attempt stores the exact question snapshot used for that attempt.

## Randomized Papers

Weekly exams sample from the corresponding week's bank and try to cover:

- Easy: core facts, true/false, fill-in;
- Medium: single-choice, multiple-choice, scenario judgment;
- Hard: short answers and cross-concept explanations.

The selected question IDs and order are stored in `exam_attempt_questions`, so an old report remains reproducible even after the bank changes later.

## Stage Exams

The current milestones are:

1. Weeks 0–4: Foundations;
2. Weeks 5–8: LLM Applications & Basic RAG;
3. Weeks 9–12: Advanced RAG & Agents;
4. Weeks 13–16: Platform, Governance & Deployment;
5. Weeks 17–18: Advanced & Capstone.

Stage exams sample across multiple weeks instead of reusing one fixed weekly paper.

## Mistake Book

The mistake book is based on the latest state of each question rather than keeping every historical mistake forever:

- if the latest recorded answer is wrong, the question appears in the mistake book;
- if a later review or retake answers it correctly, it automatically leaves the unresolved list;
- historical wrong-count remains available as a weakness signal.

## Grading Model

### Objective questions

Single-choice, multiple-choice, true/false, and fill-in questions are graded deterministically against standard answers. No LLM is required, so the same submitted answers produce the same score.

### Short answers

Short answers are graded against explicit concept rubrics. If a question expects four concepts and an answer covers three, it receives proportional partial credit. The score report shows matched concepts, missing concepts, and earned/max points.

## Coding-Exam Execution Boundary

`app/code_runner.py` defines a common `CodeRunner` boundary for future Python/RAG/Agent coding exams.

The default implementation is `DisabledCodeRunner`: **the application does not execute arbitrary learner code directly on the host**. A future coding grader should use an isolated container or other sandbox and score against pytest/test-case results.

## UI Direction

The app is designed as a learning workspace rather than a traditional admin panel. Its interaction language is inspired by Memos for quick capture, AFFiNE for knowledge-workspace hierarchy, and Tabler for mature navigation/card patterns. The implementation uses original CSS rather than copying third-party pages.

## Run with Python

Python 3.11+ is recommended.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Linux / macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:8765`.

## Docker Compose

```bash
docker compose up -d --build
```

Open `http://127.0.0.1:8765`.

Learning data is stored in `data/learning.db`. The Compose configuration mounts `./data` to `/data`, so rebuilding the image does not remove progress.

## Data Model

- `lesson_progress`: lesson state, reading/completion percentage, and best system-generated exam score.
- `exam_attempts`: one row per exam attempt with start/submission time, score, percentage, pass mark, and result.
- `exam_answers`: raw submitted answer, earned/max points, correctness, and rubric feedback per question.
- `exam_v2_meta`: attempt type, scope, localized title, and random seed for randomized weekly exams, stage exams, and mistake review.
- `exam_attempt_questions`: exact selected question order, source week, difficulty, and knowledge snapshot for each randomized attempt.
- `thoughts`: personal Markdown notes, tags, and related lesson.
- `resources`: external URL, notes, tags, and related lesson.

## Backup

Use “Export backup” in the sidebar or open `http://127.0.0.1:8765/backup.json`. Exam attempts, answer details, V2 metadata, and paper snapshots are included.

## Security Boundary

The current version is designed as a personal local learning tool and has no login system by default. Add authentication and a reverse proxy before exposing it to a LAN or public internet. User Markdown is sanitized and external links are restricted to `http://` and `https://`. Coding-exam execution is disabled by default and must use an isolated execution environment when enabled later.

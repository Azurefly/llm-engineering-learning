# Local Learning App

This repository includes a local-first learning and examination app in addition to the Markdown curriculum.

## Features

- Chinese / English course switching with shared progress.
- Reading progress tracking; manual reading progress is capped below 100%.
- A dedicated Exam Center: start an attempt, answer questions, submit, system-grade, view score reports, and retake.
- Course scores **cannot be entered manually**. Only the exam engine can write a score.
- Passing the configured exam automatically marks the lesson 100% / completed; failing keeps it in progress.
- Single-choice, multiple-choice, true/false, and fill-in questions use deterministic automatic grading.
- Short answers receive partial credit against explicit concept rubrics, with matched and missing concepts shown in the report.
- Every attempt stores raw answers, per-question scores, total score, and pass/fail status.
- Markdown thoughts linked to lessons with tags.
- External resource library for papers, tutorials, videos, blogs, and GitHub projects.
- Local SQLite storage with no external database.
- JSON backup includes progress, thoughts, resources, exam attempts, and answer details.
- Direct Python startup plus Docker / Docker Compose.

## Exam Flow

```text
Study lesson
  ↓
Open Exam Center / lesson exam card
  ↓
Start exam (creates an independent Attempt)
  ↓
Answer questions
  ↓
Submit
  ↓
Automatic system grading
  ↓
Score report + per-question feedback
  ↓
Pass → lesson 100% / completed
Fail → lesson stays in progress; retake allowed
```

Weeks 0–2 currently use mixed question types. Weeks 3–18 have checkpoint exams configured, and the engine is ready for larger question banks.

## Grading Model

### Objective questions

Single-choice, multiple-choice, true/false, and fill-in questions are graded deterministically against standard answers. No LLM is required, so the same submitted answers produce the same score.

### Short answers

Short answers are graded against explicit concept rubrics. If a question expects four concepts and an answer covers three, it receives proportional partial credit. The score report shows matched concepts, missing concepts, and earned/max points.

This approach is local, reproducible, transparent, and auditable. A future optional local-LLM / LiteLLM semantic grader can be added on top, while keeping fixed rubrics and audit records as the source of truth.

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
- `thoughts`: personal Markdown notes, tags, and related lesson.
- `resources`: external URL, notes, tags, and related lesson.

## Backup

Use “Export backup” in the sidebar or open `http://127.0.0.1:8765/backup.json`. Exam attempts and answer details are included.

## Security Boundary

The current version is designed as a personal local learning tool and has no login system by default. Add authentication and a reverse proxy before exposing it to a LAN or public internet. User Markdown is sanitized and external links are restricted to `http://` and `https://`.

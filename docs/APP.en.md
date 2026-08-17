# Local Learning Application

This is a local-first LLM engineering learning and assessment application designed for long-term personal use. The stable runtime entrypoint is `app.current:app`.

For the current architecture and implementation details, see [V5: Sequential Adaptive Testing & Long-Term Local Operation](V5.en.md).

## Current capabilities

- Bilingual Week 0-18 course reading and shared progress;
- system-graded exams with no manual score entry;
- randomized weekly exams, stage exams, mistake review, timers, autosave, and timeout submission;
- deterministic grading for objective items and strict rubric grading for short answers;
- roughly 190+ questions with an automated question-bank quality gate;
- immutable historical question snapshots;
- Python coding labs with optional Docker Sandbox + pytest grading;
- knowledge mastery, six-domain capability profile, and weak-area recommendations;
- sequential computerized adaptive testing (CAT), selecting each next question after grading the current one;
- resumable and abandonable CAT sessions;
- Markdown thoughts, tags, and course relationships;
- saved external learning resources;
- global search across courses, thoughts, and resources;
- local SQLite storage, rolling automatic backup, full JSON export and validated restore;
- local diagnostics and browser-request hardening.

## Run with Python

Python 3.11 or 3.12 is recommended. Prefer the dependency versions verified by CI:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.lock.txt
python run.py
```

Linux / macOS:

```bash
source .venv/bin/activate
pip install -r requirements.lock.txt
python run.py
```

Open `http://127.0.0.1:8765`.

Python mode stores data in:

```text
data/learning.db
```

`data/*` is ignored by Git.

## Docker Compose

```bash
docker compose up -d --build
```

Open `http://127.0.0.1:8765`.

Docker uses the named volume:

```text
llm-engineering-learning-data
```

The database is stored at `/data/learning.db` inside the container. A named volume avoids host UID/permission differences across Linux, macOS, and Windows.

Normal shutdown preserves data:

```bash
docker compose down
```

Only this command explicitly deletes the Docker volume:

```bash
docker compose down -v
```

Use the in-app Data & Backup workflow for migration rather than copying the SQLite file directly.

## Main pages

| Page | Path |
|---|---|
| Learning dashboard | `/` |
| Adaptive mastery profile | `/adaptive` |
| Sequential adaptive test | `/adaptive-test` |
| Exam center | `/exam-lab` |
| Coding labs | `/coding-labs` |
| Mistake book | `/mistakes` |
| Score history | `/exam-history` |
| Thoughts | `/thoughts` |
| External resources | `/resources` |
| Global search | `/search` |
| Data & backup | `/data-management` |
| Diagnostics | `/diagnostics` |

## Data protection

Data & Backup supports full JSON export, format validation, explicit destructive-restore confirmation, automatic pre-restore snapshots, transactional rollback, legacy-backup compatibility, and validation of restored URLs and critical ranges.

Rolling startup backups are enabled by default:

```text
LLM_AUTO_BACKUP=1
LLM_AUTO_BACKUP_HOURS=24
LLM_AUTO_BACKUP_KEEP=10
```

## Coding labs

Arbitrary learner code is disabled by default. Build the isolated runner first:

```bash
docker build -t llm-learning-sandbox:py312 sandbox
```

Then configure:

```text
LLM_CODE_RUNNER=docker
LLM_CODE_RUNNER_IMAGE=llm-learning-sandbox:py312
```

The coding sandbox uses no network, resource limits, a non-root user, a read-only workspace, dropped capabilities, and is exercised by a real CI smoke test.

## Security boundary

The default product scope is a single-user local application:

- Python listens on `127.0.0.1` by default;
- Docker publishes only `127.0.0.1:8765`;
- Trusted Host enforcement;
- cross-site write blocking;
- sanitized Markdown HTML;
- HTTP(S)-only external resource URLs;
- security response headers;
- no-store caching on sensitive JSON endpoints.

If the application is exposed to a LAN or public network, add authentication and a reverse proxy. That is outside the default single-user local deployment scope.

## Health and diagnostics

Basic health endpoint:

```text
GET /health
```

Full diagnostics:

```text
GET /diagnostics
GET /api/diagnostics
```

Diagnostics cover SQLite integrity/WAL/busy timeout, question-bank quality, Code Runner configuration, and backup state.

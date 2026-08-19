# Local Learning Application

This is a local-first LLM engineering learning and assessment application with **multi-user registration/login and physically isolated learning data per account**. The stable runtime entrypoint is `app.current:app`.

For the current architecture and implementation details, see [V5: Sequential Adaptive Testing & Long-Term Local Operation](V5.en.md). For authentication and isolation details, see [Multi-User Registration & Data Isolation](MULTI_USER.en.md).

## Current capabilities

- self-registration, login, and logout for multiple users;
- a separate SQLite learning database and backup directory per user;
- bilingual Week 0-18 course reading and shared progress within each account;
- system-graded exams with no manual score entry;
- randomized weekly exams, stage exams, mistake review, timers, autosave, and timeout submission;
- deterministic grading for objective items and strict rubric grading for short answers;
- roughly 190+ questions with an automated question-bank quality gate;
- immutable historical question snapshots;
- Week 2-18 Python coding labs with optional Docker Sandbox + pytest grading;
- knowledge mastery, six-domain capability profile, and weak-area recommendations;
- sequential computerized adaptive testing (CAT), selecting each next question after grading the current one;
- resumable and abandonable CAT sessions;
- Markdown thoughts, tags, and course relationships;
- saved external learning resources;
- global search across courses and the signed-in user's thoughts/resources;
- local SQLite WAL storage, rolling automatic backup, full JSON export and validated restore;
- local diagnostics and browser-request hardening.

## Registration and login

Opening a protected page without a session redirects to:

```text
/login
```

Self-registration is enabled by default:

```text
/register
LLM_ALLOW_REGISTRATION=1
```

After creating the desired accounts, new registration can be disabled without affecting existing sign-ins:

```text
LLM_ALLOW_REGISTRATION=0
```

Passwords are never stored in plaintext. Browser sessions use an HttpOnly, SameSite=Lax cookie. The default lifetime is 30 days:

```text
LLM_SESSION_DAYS=30
```

For an HTTPS reverse-proxy deployment, secure cookies can be forced with:

```text
LLM_COOKIE_SECURE=1
```

## Per-user data isolation

Account/session data and learning data are separated:

```text
data/
├─ accounts.db
└─ users/
   ├─ <storage-key-A>/
   │  ├─ learning.db
   │  └─ backups/
   └─ <storage-key-B>/
      ├─ learning.db
      └─ backups/
```

`accounts.db` stores users and sessions only. Each user's `learning.db` contains that user's:

- lesson progress and system-generated scores;
- exams, answers, mistakes, and immutable question snapshots;
- timed-exam drafts and autosave state;
- coding-lab results;
- mastery analytics and adaptive-test sessions;
- thoughts;
- saved external resources;
- backup/restore data.

Isolation therefore does not depend on every SQL statement remembering a `user_id` filter; different users use different SQLite learning files.

### Upgrade from the previous single-user version

If an existing installation already contains learning history in:

```text
data/learning.db
```

the first successfully registered account automatically copies and inherits that database. The original legacy file is not deleted. Later users start with independent empty learning databases.

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

Python mode stores data under:

```text
data/accounts.db
data/users/<storage-key>/learning.db
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

Inside the volume:

```text
/data/accounts.db
/data/users/<storage-key>/learning.db
/data/users/<storage-key>/backups/
```

Normal shutdown preserves all accounts and data:

```bash
docker compose down
```

Only this command explicitly deletes the entire Docker volume, including **all accounts and all users' learning data**:

```bash
docker compose down -v
```

Use the in-app Data & Backup workflow for learning-data migration rather than copying a live SQLite database directly.

## Main pages

| Page | Path |
|---|---|
| Login | `/login` |
| Register | `/register` |
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

Data & Backup operates only on the **currently signed-in user's** learning database. It supports full JSON export, format validation, explicit destructive-restore confirmation, automatic per-user pre-restore snapshots, transactional rollback, legacy-backup compatibility, and validation of restored URLs and critical ranges.

Authentication accounts, password hashes, sessions, and other users' data are never included in an individual learning JSON backup.

Rolling backups are checked when a user space is initialized:

```text
LLM_AUTO_BACKUP=1
LLM_AUTO_BACKUP_HOURS=24
LLM_AUTO_BACKUP_KEEP=10
```

Backups live in that user's own `backups/` directory.

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

The default deployment remains local-first or intended for a controlled LAN:

- unauthenticated users cannot read or write learning data;
- Python listens on `127.0.0.1` by default;
- Docker publishes only `127.0.0.1:8765` by default;
- passwords are securely hashed and never stored in plaintext;
- session cookies are HttpOnly + SameSite=Lax;
- Trusted Host enforcement;
- cross-site write blocking;
- sanitized Markdown HTML;
- HTTP(S)-only external resource URLs;
- security response headers;
- no-store caching on sensitive JSON endpoints.

For LAN exposure, use an HTTPS reverse proxy and configure for example:

```text
LLM_ALLOWED_HOSTS=learning.local,192.168.1.10
LLM_COOKIE_SECURE=1
```

If open self-registration is not wanted, also configure:

```text
LLM_ALLOW_REGISTRATION=0
```

## Health and diagnostics

Basic health endpoint (public for container health checks):

```text
GET /health
```

Full diagnostics (authenticated and scoped to the signed-in user's learning database):

```text
GET /diagnostics
GET /api/diagnostics
```

Diagnostics cover the active user's SQLite integrity/WAL/busy timeout, question-bank quality, Code Runner configuration, and that user's backup state.

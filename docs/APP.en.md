# Local Learning App

This repository includes a local-first lightweight learning app in addition to the Markdown curriculum.

## Features

- Chinese / English course switching with shared progress.
- Course reading and 0–100% progress tracking.
- Weekly test score tracking.
- Markdown thoughts linked to lessons with tags.
- External resource library for papers, tutorials, videos, blogs, and GitHub projects.
- Local SQLite storage with no external database.
- JSON backup export.
- Direct Python startup.
- Docker and Docker Compose startup.

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

- `lesson_progress`: status, completion percentage, and test score.
- `thoughts`: personal Markdown notes, tags, and related lesson.
- `resources`: external URL, notes, tags, and related lesson.

## Backup

Use “Export backup” in the sidebar or open `http://127.0.0.1:8765/backup.json`.

## Security Boundary

The current version is designed as a personal local learning tool and has no login system by default. Add authentication and a reverse proxy before exposing it to a LAN or public internet. User Markdown is sanitized and external links are restricted to `http://` and `https://`.

# Multi-User Login, Registration, and Data Isolation

The application supports self-registration, login, logout, and physically isolated learning data per account. Superadmins additionally govern accounts, control public registration at runtime, and receive cross-user learning-progress reports.

## Data layout

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

`accounts.db` stores accounts, sessions, and global runtime settings. Progress, exams, answers, mistakes, coding submissions, notes, resources, mastery data, adaptive sessions, and backups live in each user's own directory.

Isolation therefore does not depend only on application-level `WHERE user_id=?` filters; different users use different SQLite learning databases.

## Registration and runtime policy

Before any administrator has saved a registration policy, the initial default comes from:

```text
LLM_ALLOW_REGISTRATION=1
```

The first successful account becomes `SUPERADMIN`. A superadmin can then open:

```text
/admin/users
```

and enable or disable public registration immediately. The setting is persisted in `accounts.db.system_settings` and does not require a Python or Docker restart.

When registration is disabled:

- `/register` returns HTTP `403`;
- existing users can still sign in;
- superadmins can still provision accounts manually.

Once a runtime policy has been saved, the database setting takes precedence over `LLM_ALLOW_REGISTRATION`.

Registration rules:

- username: 3-32 characters;
- Unicode letters/digits plus `. _ -` are supported;
- optional display name up to 64 characters;
- password: 8-128 characters;
- usernames are normalized with NFKC + casefold before uniqueness checks.

## Passwords and sessions

Passwords are never stored in plaintext. The application uses PBKDF2-HMAC-SHA256 with a random salt.

A successful login creates a random session token. Only the SHA-256 digest of that token is stored in the database. The browser cookie uses:

- `HttpOnly`;
- `SameSite=Lax`;
- `Secure` when HTTPS is used or explicitly configured.

Default session lifetime is 30 days:

```text
LLM_SESSION_DAYS=30
```

Allowed range: 1-90 days.

For HTTPS reverse-proxy deployments, you can force secure cookies:

```text
LLM_COOKIE_SECURE=1
```

## Superadmin learning-progress reports

Superadmins can open:

```text
/admin/report
/admin/report/data
/admin/users/<id>/progress
```

to view all-user overall progress, Week 0-18 completion, system-exam summaries, coding-practice summaries, activity, and per-user lesson progress.

Cross-user reading is explicitly limited to the reporting whitelist:

```text
lesson_progress
exam_attempts
code_attempts
```

The reporting layer does not output:

- thought/note content;
- saved-resource body/content;
- learner source code;
- password hashes;
- storage keys;
- user database paths.

Physical per-user isolation therefore remains the storage boundary; the superadmin role receives a controlled **read-only progress reporting capability**, not unrestricted browsing of private learning records.

## Migration from the previous single-user version

If an existing `data/learning.db` contains learning history when upgrading:

1. the upgraded application asks for account registration/login;
2. the first successfully registered account automatically copies and claims the legacy `learning.db`;
3. later accounts start with independent empty learning databases;
4. the original legacy database is not deleted automatically.

This preserves existing single-user learning history during the upgrade.

## Isolation scope

The following are isolated per user:

- lesson progress and system-generated scores;
- exam attempts, answers, and immutable paper snapshots;
- timed-exam drafts and autosave state;
- mistake book and score history;
- coding-lab submissions and pytest scores;
- mastery profile and adaptive testing sessions;
- Markdown thoughts;
- saved external resources;
- JSON exports, pre-restore snapshots, and rolling automatic backups.

Curriculum Markdown, question-bank definitions, and coding-lab challenge definitions are shared application content rather than private user data.

## Docker

Docker Compose stores `/data` in one named volume, while user data remains separated inside that volume:

```text
/data/accounts.db
/data/users/<storage-key>/learning.db
/data/users/<storage-key>/backups/
```

`docker compose down` keeps all accounts, settings, and learning data. `docker compose down -v` deletes the entire named volume, including every account and every user's learning data.

## Security boundary

The default deployment still binds only to `127.0.0.1:8765`. When exposing it to a LAN:

- use an HTTPS reverse proxy;
- configure `LLM_ALLOWED_HOSTS`;
- consider `LLM_COOKIE_SECURE=1`;
- manage self-registration from the superadmin UI; the environment variable is only the initial default.

Application authentication, controlled admin reporting, and per-user data isolation do not replace TLS, firewalling, reverse-proxy configuration, and host security when exposed beyond localhost.

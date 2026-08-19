# Multi-User Login, Registration, and Data Isolation

The application supports self-registration, login, logout, and physically isolated learning data per account.

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

`accounts.db` stores only accounts and sessions. Progress, exams, answers, mistakes, coding submissions, notes, resources, mastery data, adaptive sessions, and backups live in each user's own directory.

Isolation therefore does not depend only on application-level `WHERE user_id=?` filters; different users use different SQLite learning databases.

## Registration

Self-registration is enabled by default:

```text
LLM_ALLOW_REGISTRATION=1
```

Disable new registration with:

```text
LLM_ALLOW_REGISTRATION=0
```

Existing users can still sign in when registration is disabled.

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

Docker Compose still stores `/data` in one named volume, while user data remains separated inside that volume:

```text
/data/accounts.db
/data/users/<storage-key>/learning.db
/data/users/<storage-key>/backups/
```

`docker compose down` keeps all accounts and learning data. `docker compose down -v` deletes the entire named volume, including every account and every user's learning data.

## Security boundary

The default deployment still binds only to `127.0.0.1:8765`. When exposing it to a LAN:

- use an HTTPS reverse proxy;
- configure `LLM_ALLOWED_HOSTS`;
- consider `LLM_COOKIE_SECURE=1`;
- set `LLM_ALLOW_REGISTRATION=0` if open self-registration is not desired.

Application authentication and per-user data isolation do not replace TLS, firewalling, reverse-proxy configuration, and host security when exposed beyond localhost.

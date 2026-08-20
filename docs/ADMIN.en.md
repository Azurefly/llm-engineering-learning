# Superadmin, User Administration & Learning Reports

The multi-user release provides two account roles: `superadmin` and regular `user`. A superadmin governs accounts and may view **learning progress, system-exam summaries, and coding-practice summaries** across users. Private thoughts, saved-resource content, and learner source code remain outside the reporting surface.

## How the first superadmin is created

- Fresh installation: the first successfully registered account becomes `superadmin` automatically.
- Existing multi-user installation: if the account database has no superadmin, the earliest existing account is promoted during schema migration.
- A superadmin may promote other users to `superadmin` from User Administration.
- The system always protects at least one enabled superadmin. A superadmin cannot disable or demote the currently signed-in superadmin account from the administration page.

## Administration entry points

```text
/admin/users                 User Administration
/admin/report                Learning Operations Big Screen
/admin/report/data           Learning report JSON
/admin/users/<id>/progress   Per-user Week 0-18 progress detail
```

Regular users receive HTTP `403` for these superadmin routes.

## User Administration

A superadmin can:

- view username, display name, role, registration time, last-login time, account state, and active-session count;
- create accounts even when public registration is disabled;
- update usernames and display names;
- enable or disable accounts;
- promote a regular user to superadmin, or demote another superadmin when the last-admin safety rule permits it;
- reset another user's password;
- revoke all of that user's existing sessions when a password is reset.

To protect learning history, the administration UI intentionally does not expose a hard-delete operation. Prefer **Disable account** so the user's physically isolated database and backups remain intact.

## Learning Operations Big Screen

`/admin/report` is a fullscreen-capable superadmin dashboard and refreshes every 60 seconds by default.

It includes:

- registered, enabled, learning, and recent-active user counts;
- average learning progress across all accounts;
- Week 0-18 average progress, started-user count, and completed-user count;
- total submitted system exams and pass rate;
- coding-practice attempt count and pass rate;
- user progress distribution;
- a per-user table showing overall progress, completed lessons, current week, exam performance, coding performance, and last activity.

Selecting a learner opens `/admin/users/<id>/progress`, which shows their Week 0-18 lesson progress and system score summary.

### Reporting privacy boundary

The reporting layer reads only the following whitelisted learning tables from each physically isolated user database:

```text
lesson_progress
exam_attempts
code_attempts
```

It does **not** expose:

```text
thoughts
saved-resource body/content
code_attempts.source_code
password_hash
storage_key
user database paths
```

This lets superadmins manage completion and learning operations without turning the admin role into unrestricted access to private learner knowledge records.

## Public registration control

A superadmin can enable or disable public self-registration directly from **User Administration**.

The setting is stored in `accounts.db` under `system_settings` and takes effect immediately; Python or Docker does not need to be restarted.

When registration is disabled:

- `/register` immediately returns HTTP `403`;
- existing users can still sign in;
- superadmins can still provision accounts manually from User Administration.

The environment variable:

```text
LLM_ALLOW_REGISTRATION=1
```

now serves only as the **initial default before an administrator has saved a runtime policy**. After the first admin toggle, the value persisted in `accounts.db` takes precedence.

## Self-service password changes

Every signed-in user can open:

```text
/account
```

Users can change their own username, display name, and password. Password changes require the current password. After success, all sessions for the account are revoked and the user must sign in again with the new password.

## Data-isolation and reporting boundary

Global account identity and settings remain in:

```text
data/accounts.db
```

Learning data remains physically isolated:

```text
data/users/<storage-key>/learning.db
```

Cross-user reading is limited to the progress/reporting whitelist above. The dashboard does not merge user databases and does not modify learner progress, exams, or coding results.

## Security behavior

- Passwords are stored using salted PBKDF2-HMAC-SHA256, never as plaintext.
- The session cookie is HttpOnly.
- Only a SHA-256 digest of the session token is stored in SQLite.
- Password reset and account disable operations revoke the target user's active sessions.
- Regular users cannot invoke superadmin routes.
- Report JSON excludes password hashes, storage keys, private thoughts, and learner source code.
- CI validates cross-user progress reporting, Docker access boundaries, and runtime registration enable/disable behavior.

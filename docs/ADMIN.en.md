# Superadmin & User Administration

The multi-user release provides two account roles: `superadmin` and regular `user`. A superadmin manages **account metadata and access**, but does not automatically gain access to another user's learning database.

## How the first superadmin is created

- Fresh installation: the first successfully registered account becomes `superadmin` automatically.
- Existing multi-user installation: if the account database has no superadmin, the earliest existing account is promoted during schema migration.
- A superadmin may promote other users to `superadmin` from User Administration.
- The system always protects at least one enabled superadmin. A superadmin cannot disable or demote the currently signed-in superadmin account from the administration page.

## User Administration

Sign in as a superadmin and open:

```text
/admin/users
```

The sidebar also shows **User Administration / ADMIN**. A regular user receives HTTP `403` for this route.

## Supported operations

A superadmin can:

- view username, display name, role, registration time, last-login time, account state, and active-session count;
- create accounts even when public registration is disabled with `LLM_ALLOW_REGISTRATION=0`;
- update usernames and display names;
- enable or disable accounts;
- promote a regular user to superadmin, or demote another superadmin when the last-admin safety rule permits it;
- reset another user's password;
- revoke all of that user's existing sessions when a password is reset.

To protect learning history, the administration UI intentionally does not expose a hard-delete operation. Prefer **Disable account** so the user's physically isolated database and backups remain intact.

## Self-service password changes

Every signed-in user can open:

```text
/account
```

Users can change their own username, display name, and password. Password changes require the current password. After success, all sessions for the account are revoked and the user must sign in again with the new password.

## Data-isolation boundary

Superadmins manage the global account database:

```text
data/accounts.db
```

Learning data remains physically isolated:

```text
data/users/<storage-key>/learning.db
```

User Administration does not open, merge, or display another user's progress, exam answers, mistake book, coding attempts, thoughts, resources, adaptive mastery profile, or private backups.

## Registration control

Public self-registration remains controlled by:

```text
LLM_ALLOW_REGISTRATION=1
```

Disable it with:

```text
LLM_ALLOW_REGISTRATION=0
```

When public registration is disabled, a superadmin can still create accounts from User Administration.

## Security behavior

- Passwords are stored using salted PBKDF2-HMAC-SHA256, never as plaintext.
- The session cookie is HttpOnly.
- Only a SHA-256 digest of the session token is stored in SQLite.
- Password reset and account disable operations revoke the target user's active sessions.
- Regular users cannot invoke superadmin routes.
- CI validates these rules in both Python tests and a real Docker application smoke test.

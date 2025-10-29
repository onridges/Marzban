# Authentication design notes (short)

This short note outlines the current recommended authentication approach and small improvements for the Marzban project.

Contract (inputs/outputs):
- Inputs: username/email + password or API token.
- Outputs: JWT access token (short lived) and optional refresh token.

Proposal (minimal safe changes):

1) Password storage
   - Use a strong hashing algorithm such as bcrypt or Argon2 (libraries: passlib, argon2-cffi).
   - Salt and hash per-user. Do not store plaintext or reversible encryption.

2) Tokens
   - Issue JWT access tokens (short expiry, e.g. 15m) signed with `SECRET_KEY`.
   - Optionally issue refresh tokens stored server-side with rotation to allow revocation.

3) Login flow
   - POST /auth/login with credentials. On success return access token and refresh token.
   - Record last-login timestamp and optional device metadata.

4) Password reset
   - Use time-limited reset tokens sent to user email. Implement rate-limit and CAPTCHA if needed.

5) Admin and emergency workflows
   - Provide an endpoint for admin to rotate secrets and to revoke all tokens (requires re-issue of SECRET_KEY or token blacklist).

Edge cases to consider:

- Brute-force: rate-limit login attempts and lockout after repeated failures.
- Token theft: support token revocation and short-lived access tokens.
- Migration: if migrating from legacy password scheme, add a migration path to re-hash on first login.

Small next steps (low-risk):

- Add passlib[bcrypt] to requirements and use it in the user model for hashing.
- Add tests for login/logout and token expiry handling.

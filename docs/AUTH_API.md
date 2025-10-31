# Authentication API (examples)

This document shows example requests and responses for the authentication endpoints provided by the backend.

Base path: `/api`

1) Register (JSON)

Request

POST /api/register

Body (JSON):

{
  "username": "alice",
  "password": "s3cret"
}

Success response (200):

{
  "detail": "User created"
}

Errors:
- 400: missing username or password
- 409: user already exists


2) Token (login) — OAuth2 password grant (form)

Request

POST /api/token

Form body:

- username
- password

Success response (200):

{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "refresh_token": "<refresh-token>"
}

Errors:
- 401: incorrect username or password


3) Refresh token

Request

POST /api/token/refresh

Body (JSON):

{
  "refresh_token": "<refresh-token>"
}

Success response (200):

{
  "access_token": "<jwt>",
  "token_type": "bearer"
}

Errors:
- 400: missing refresh_token
- 401: invalid or expired refresh token


4) Logout (revoke refresh token)

Request

POST /api/logout

Body (JSON):

{
  "refresh_token": "<refresh-token>"
}

Success response (200):

{
  "detail": "Logged out"
}

Errors:
- 400: missing refresh_token
- 404: refresh token not found


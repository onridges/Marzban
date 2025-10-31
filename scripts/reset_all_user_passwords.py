#!/usr/bin/env python3
"""
Reset all non-admin users' passwords to a specified value.

This script updates the `users.hashed_password` field for all users and
revokes all existing user refresh tokens to ensure re-login is required.

Usage:
  Run from project root `Marzban/` directory:
    python3 scripts/reset_all_user_passwords.py
"""

import sys
from sqlalchemy import text

# Ensure local imports work when executed from project root
try:
    from app.db import get_db
    from app.models.admin import pwd_context
except Exception:
    # Fallback: add current directory to path and retry
    import os
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    sys.path.insert(0, PROJECT_ROOT)
    from app.db import get_db
    from app.models.admin import pwd_context


NEW_PASSWORD = "p@ssw0rd"


def main():
    db = next(get_db())
    try:
        # Hash the new password using the same context used by login verification
        hashed = pwd_context.hash(NEW_PASSWORD)

        # Update all user hashed_passwords
        res = db.execute(text("UPDATE users SET hashed_password = :hp"), {"hp": hashed})

        # Revoke all existing refresh tokens for users (forces re-login)
        db.execute(text("UPDATE refresh_tokens SET revoked = 1"))

        db.commit()

        # Print outcome; rowcount may be None for some DBs/drivers
        try:
            updated = getattr(res, "rowcount", None)
        except Exception:
            updated = None
        print(f"Passwords reset for all users. Rows affected: {updated}")
        print("All refresh tokens revoked.")
    except Exception as e:
        db.rollback()
        print("Error resetting passwords:", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
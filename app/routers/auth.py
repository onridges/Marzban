from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.db import get_db, crud
from sqlalchemy import text
from app.db import Session
from app.models.admin import pwd_context
from app.utils.jwt import create_user_token, decode_token
from config import REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter(tags=["Auth"], prefix="/api")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str | None = None


class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str


class UserResponse(BaseModel):
    username: str
    email: str
    created_at: datetime


@router.post("/register", response_model=dict)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Public user registration. Accepts JSON {"username": "u", "email": "e", "password": "p"}.
    This endpoint creates a minimal user record (no proxies)."""
    username = payload.username
    email = payload.email
    password = payload.password
    
    try:
        if not username or not password:
            raise HTTPException(status_code=400, detail="username and password required")

        # Avoid complex ORM joins for MySQL compatibility during existence check
        existing = db.execute(text("SELECT 1 FROM users WHERE username = :u LIMIT 1"), {"u": username}).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="User already exists")

        hashed = pwd_context.hash(password)
        # Insert user via SQL to avoid ORM mapping issues with legacy schemas
        db.execute(
            text(
                """
                INSERT INTO users (
                    username, hashed_password, status, used_traffic,
                    data_limit_reset_strategy, role, created_at
                ) VALUES (
                    :username, :hashed_password, :status, :used_traffic,
                    :data_limit_reset_strategy, :role, :created_at
                )
                """
            ),
            {
                "username": username,
                "hashed_password": hashed,
                "status": "active",
                "used_traffic": 0,
                "data_limit_reset_strategy": "no_reset",
                "role": "user",
                "created_at": datetime.utcnow(),
            },
        )
        db.commit()
        return {"detail": "User created"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("[register] unexpected error:\n" + traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/token", response_model=TokenResponse)
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 compatible token login, get an access token for future requests"""
    # 使用原生SQL避免ORM对不存在列的访问
    row = db.execute(
        text("SELECT id, username, hashed_password FROM users WHERE username = :u LIMIT 1"),
        {"u": form_data.username},
    ).fetchone()
    if not row or not row.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not pwd_context.verify(form_data.password, row.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_user_token(row.username)
    # 生成并保存刷新令牌到数据库
    import secrets
    raw_refresh = secrets.token_urlsafe(32)
    refresh_hash = pwd_context.hash(raw_refresh)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.execute(
        text(
            """
            INSERT INTO refresh_tokens (user_id, token_hash, created_at, expires_at, revoked)
            VALUES (:user_id, :token_hash, :created_at, :expires_at, :revoked)
            """
        ),
        {
            "user_id": row.id,
            "token_hash": refresh_hash,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "revoked": False,
        },
    )
    db.commit()
    refresh_token = raw_refresh

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    # 简化：当前不支持JWT型刷新令牌；建议改用 /api/token/refresh 接口（数据库存储刷新令牌）
    raise HTTPException(status_code=400, detail="Refresh token flow not supported here")


@router.post("/logout", response_model=dict)
def logout(payload: dict, db: Session = Depends(get_db)):
    """Revoke a refresh token. Body: {"refresh_token": "..."}"""
    rt = payload.get("refresh_token")
    if not rt:
        raise HTTPException(status_code=400, detail="refresh_token required")

    # 查找有效刷新令牌并撤销
    rows = db.execute(
        text(
            """
            SELECT id, token_hash FROM refresh_tokens
            WHERE expires_at > :now AND revoked = :revoked
            """
        ),
        {"now": datetime.utcnow(), "revoked": False},
    ).fetchall()

    token_id = None
    for row in rows:
        if pwd_context.verify(rt, row.token_hash):
            token_id = row.id
            break

    if not token_id:
        raise HTTPException(status_code=404, detail="Refresh token not found")

    db.execute(text("UPDATE refresh_tokens SET revoked = :revoked WHERE id = :id"), {"revoked": True, "id": token_id})
    db.commit()
    return {"detail": "Logged out"}


@router.post("/token/refresh", response_model=TokenResponse)
def refresh_token(payload: dict, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access token. Body: {"refresh_token": "..."}"""
    rt = payload.get("refresh_token")
    if not rt:
        raise HTTPException(status_code=400, detail="refresh_token required")

    # 查找有效刷新令牌并验证
    rows = db.execute(
        text(
            """
            SELECT rt.id, rt.user_id, rt.token_hash, rt.expires_at, rt.revoked, u.username
            FROM refresh_tokens rt
            JOIN users u ON rt.user_id = u.id
            WHERE rt.expires_at > :now AND rt.revoked = :revoked
            """
        ),
        {"now": datetime.utcnow(), "revoked": False},
    ).fetchall()

    user_id = None
    username = None
    for row in rows:
        if pwd_context.verify(rt, row.token_hash):
            user_id = row.user_id
            username = row.username
            break

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    access_token = create_user_token(username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", response_model=dict)
def logout(payload: dict, db: Session = Depends(get_db)):
    """Revoke a refresh token. Body: {"refresh_token": "..."}"""
    rt = payload.get("refresh_token")
    if not rt:
        raise HTTPException(status_code=400, detail="refresh_token required")

    import hashlib
    token_hash = hashlib.sha256(rt.encode('utf-8')).hexdigest()
    revoked = crud.revoke_refresh_token(db, token_hash)
    if not revoked:
        raise HTTPException(status_code=404, detail="Refresh token not found")
    return {"detail": "Logged out"}

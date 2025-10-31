from datetime import datetime, timedelta
import os
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user_auth import (
    Token, UserRegister, RefreshToken, UserAuth,
    verify_password, get_password_hash
)
from app.utils import responses
from app.utils.jwt import create_user_token
from config import REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter(tags=["Authentication"], prefix="/api", responses={401: responses._401})


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"]
    return request.client.host if request.client else "unknown"


@router.post("/register", status_code=status.HTTP_200_OK)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    """用户注册"""
    from app.db import crud
    
    # 检查用户名是否已存在
    if crud.get_user(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    try:
        user = crud.create_user(db, {
            "username": user_data.username,
            "hashed_password": hashed_password,
            "role": "user"
        })
        
        # 创建用户资料
        if user_data.email or user_data.full_name:
            db.execute(
                "INSERT INTO user_profiles (user_id, email, full_name, created_at, updated_at) "
                "VALUES (:user_id, :email, :full_name, :created_at, :updated_at)",
                {
                    "user_id": user.id,
                    "email": user_data.email,
                    "full_name": user_data.full_name,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )
            db.commit()
        
        return {"detail": "User created"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )


@router.post("/token", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """用户登录"""
    from app.db import crud
    
    # 获取用户
    user = crud.get_user(db, form_data.username)
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token = create_user_token(user.username)
    
    # 创建刷新令牌
    refresh_token = secrets.token_urlsafe(32)
    refresh_token_hash = get_password_hash(refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # 存储刷新令牌
    db.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, created_at, expires_at, revoked) "
        "VALUES (:user_id, :token_hash, :created_at, :expires_at, :revoked)",
        {
            "user_id": user.id,
            "token_hash": refresh_token_hash,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "revoked": False
        }
    )
    db.commit()
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token
    )


@router.post("/token/refresh", response_model=Token)
def refresh_token(
    token_data: RefreshToken,
    db: Session = Depends(get_db),
):
    """刷新访问令牌"""
    # 查找刷新令牌
    result = db.execute(
        "SELECT rt.id, rt.user_id, rt.token_hash, rt.expires_at, rt.revoked, u.username "
        "FROM refresh_tokens rt "
        "JOIN users u ON rt.user_id = u.id "
        "WHERE rt.expires_at > :now AND rt.revoked = :revoked",
        {"now": datetime.utcnow(), "revoked": False}
    ).fetchall()
    
    # 验证刷新令牌
    user_id = None
    username = None
    token_id = None
    
    for row in result:
        if verify_password(token_data.refresh_token, row.token_hash):
            user_id = row.user_id
            username = row.username
            token_id = row.id
            break
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建新的访问令牌
    access_token = create_user_token(username)
    
    return Token(
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    token_data: RefreshToken,
    db: Session = Depends(get_db),
):
    """用户登出"""
    # 查找刷新令牌
    result = db.execute(
        "SELECT rt.id, rt.token_hash "
        "FROM refresh_tokens rt "
        "WHERE rt.expires_at > :now AND rt.revoked = :revoked",
        {"now": datetime.utcnow(), "revoked": False}
    ).fetchall()
    
    # 验证并撤销刷新令牌
    token_id = None
    
    for row in result:
        if verify_password(token_data.refresh_token, row.token_hash):
            token_id = row.id
            break
    
    if not token_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh token not found"
        )
    
    # 撤销刷新令牌
    db.execute(
        "UPDATE refresh_tokens SET revoked = :revoked WHERE id = :id",
        {"revoked": True, "id": token_id}
    )
    db.commit()
    
    return {"detail": "Logged out"}
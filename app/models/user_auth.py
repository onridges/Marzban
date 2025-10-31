from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from sqlalchemy.orm import Session

from app.db import get_db
from app.utils.jwt import create_user_token, get_user_payload

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2密码Bearer流程
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    """令牌载荷模型"""
    sub: str
    exp: int
    iat: int
    access: str


class UserAuth(BaseModel):
    """用户认证模型"""
    username: str
    role: str
    email: Optional[EmailStr] = None
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def get_user(cls, token: str, db: Session):
        """从令牌获取用户"""
        payload = get_user_payload(token)
        if not payload:
            return None

        from app.db import crud
        dbuser = crud.get_user(db, payload['username'])
        if not dbuser:
            return None

        return cls.model_validate(dbuser)

    @classmethod
    def get_current(cls,
                    db: Session = Depends(get_db),
                    token: str = Depends(oauth2_scheme)):
        """获取当前用户"""
        user = cls.get_user(token, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user


class UserRegister(BaseModel):
    """用户注册模型"""
    username: str
    password: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

    @field_validator("username")
    def username_validator(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    @field_validator("password")
    def password_validator(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str


class RefreshToken(BaseModel):
    """刷新令牌模型"""
    refresh_token: str


class UserProfile(BaseModel):
    """用户资料模型"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SubscriptionPlan(BaseModel):
    """订阅计划模型"""
    id: int
    name: str
    description: Optional[str] = None
    price: float
    duration_days: int
    data_limit: Optional[int] = None
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)


class OrderStatus(str):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(BaseModel):
    """订单模型"""
    id: int
    user_id: int
    plan_id: int
    amount: float
    status: str
    payment_method: Optional[str] = None
    payment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


def verify_password(plain_password, hashed_password):
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """获取密码哈希"""
    return pwd_context.hash(password)
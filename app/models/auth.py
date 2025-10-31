from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from passlib.context import CryptContext
from jose import jwt
from config import SECRET_KEY

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT设置
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


class AuthUser(Base):
    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(32), unique=True, index=True)
    email = Column(String(128), unique=True, index=True)
    hashed_password = Column(String(128))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联到现有的用户系统
    marzban_username = Column(String(32), unique=True, nullable=True)
    
    @staticmethod
    def verify_password(plain_password, hashed_password):
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password):
        """获取密码哈希"""
        return pwd_context.hash(password)
    
    def generate_tokens(self):
        """生成访问令牌和刷新令牌"""
        access_token_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token_data = {
            "sub": self.username,
            "email": self.email,
            "is_admin": self.is_admin,
            "exp": access_token_expires
        }
        
        refresh_token_data = {
            "sub": self.username,
            "type": "refresh",
            "exp": refresh_token_expires
        }
        
        access_token = jwt.encode(access_token_data, SECRET_KEY, algorithm=ALGORITHM)
        refresh_token = jwt.encode(refresh_token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
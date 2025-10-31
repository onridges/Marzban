from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    ALIPAY = "alipay"
    WECHAT = "wechat"
    STRIPE = "stripe"
    MANUAL = "manual"


class SubscriptionPlanCreate(BaseModel):
    name: str
    price: float
    duration_days: int
    data_limit_gb: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True


class SubscriptionPlan(SubscriptionPlanCreate):
    id: int
    created_at: datetime


class OrderCreate(BaseModel):
    user_id: int
    plan_id: int
    payment_method: PaymentMethod
    amount: float
    description: Optional[str] = None


class Order(OrderCreate):
    id: int
    status: PaymentStatus = PaymentStatus.PENDING
    paid_at: Optional[datetime] = None
    transaction_id: Optional[str] = None
    created_at: datetime


class PaymentCallbackBase(BaseModel):
    order_id: str
    transaction_id: str
    amount: float
    status: PaymentStatus


class AlipayCallback(PaymentCallbackBase):
    trade_no: str
    buyer_id: Optional[str] = None
    extra_data: Optional[dict] = None


class WechatCallback(PaymentCallbackBase):
    openid: Optional[str] = None
    extra_data: Optional[dict] = None


class StripeCallback(PaymentCallbackBase):
    customer_id: Optional[str] = None
    payment_intent_id: str
    extra_data: Optional[dict] = None


class PaymentResponse(BaseModel):
    order_id: int
    payment_url: str
    qr_code: Optional[str] = None
    expires_at: Optional[datetime] = None


class UserSubscription(BaseModel):
    id: int
    user_id: int
    plan_id: int
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    data_limit_gb: Optional[int] = None
    data_used_gb: float = 0
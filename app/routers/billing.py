from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.crud_billing import (
    create_subscription_plan, get_subscription_plans, get_subscription_plan,
    create_order, get_order, get_user_orders, update_order_status,
    get_user_subscription
)
from app.db.session import get_db
from app.models.billing import (
    SubscriptionPlanCreate, SubscriptionPlan, OrderCreate, Order,
    PaymentResponse, PaymentStatus, PaymentMethod, UserSubscription
)
from app.dependencies import get_current_user
from app.models.admin import Admin
from app.payment.factory import create_payment_provider

router = APIRouter(prefix="/api/billing", tags=["billing"])


# 订阅计划管理 - 管理员接口
@router.post("/plans", response_model=SubscriptionPlan, dependencies=[Depends(Admin.get_current)])
async def add_subscription_plan(plan: SubscriptionPlanCreate, db: AsyncSession = Depends(get_db)):
    """创建新的订阅计划"""
    return await create_subscription_plan(db, plan)


@router.get("/plans", response_model=List[SubscriptionPlan])
async def list_subscription_plans(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """获取所有订阅计划"""
    return await get_subscription_plans(db, active_only)


@router.get("/plans/{plan_id}", response_model=SubscriptionPlan)
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个订阅计划详情"""
    plan = await get_subscription_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="订阅计划不存在")
    return plan


# 订单管理
@router.post("/orders", response_model=PaymentResponse)
async def create_new_order(
    order: OrderCreate,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新订单并返回支付链接"""
    # 验证订阅计划是否存在
    plan = await get_subscription_plan(db, order.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="订阅计划不存在或已停用")
    
    # 验证支付金额是否正确
    if order.amount != plan.price:
        raise HTTPException(status_code=400, detail="支付金额不正确")
    
    # 创建订单
    db_order = await create_order(db, order)
    
    # 获取支付提供商
    payment_provider = create_payment_provider(order.payment_method)
    if not payment_provider:
        raise HTTPException(status_code=400, detail="不支持的支付方式")
    
    # 生成支付链接
    payment_info = await payment_provider.create_payment(db_order)
    
    return PaymentResponse(
        order_id=db_order.id,
        payment_url=payment_info.get("payment_url", ""),
        qr_code=payment_info.get("qr_code"),
        expires_at=payment_info.get("expires_at")
    )


@router.get("/orders", response_model=List[Order])
async def list_user_orders(
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的所有订单"""
    return await get_user_orders(db, user.id)


@router.get("/orders/{order_id}", response_model=Order)
async def get_order_detail(
    order_id: int,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取订单详情"""
    order = await get_order(db, order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


# 支付回调接口
@router.post("/callback/{payment_method}")
async def payment_callback(
    payment_method: PaymentMethod,
    db: AsyncSession = Depends(get_db)
):
    """支付回调接口"""
    payment_provider = create_payment_provider(payment_method)
    if not payment_provider:
        raise HTTPException(status_code=400, detail="不支持的支付方式")
    
    # 验证支付回调
    callback_result = await payment_provider.verify_callback()
    if not callback_result.get("verified", False):
        raise HTTPException(status_code=400, detail="支付验证失败")
    
    # 更新订单状态
    await update_order_status(
        db,
        callback_result["order_id"],
        PaymentStatus.PAID,
        callback_result.get("transaction_id")
    )
    
    return {"success": True}


# 用户订阅信息
@router.get("/subscription", response_model=UserSubscription)
async def get_current_subscription(
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的订阅信息"""
    subscription = await get_user_subscription(db, user.id)
    if not subscription:
        raise HTTPException(status_code=404, detail="没有有效的订阅")
    return subscription
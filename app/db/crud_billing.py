from datetime import datetime, timedelta
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import SubscriptionPlan, Order, UserSubscription, User
from app.models.billing import PaymentStatus, OrderCreate, SubscriptionPlanCreate


async def create_subscription_plan(db: AsyncSession, plan: SubscriptionPlanCreate) -> SubscriptionPlan:
    """创建订阅计划"""
    db_plan = SubscriptionPlan(
        name=plan.name,
        price=plan.price,
        duration_days=plan.duration_days,
        data_limit_gb=plan.data_limit_gb,
        description=plan.description,
        is_active=plan.is_active,
        created_at=datetime.now()
    )
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    return db_plan


async def get_subscription_plans(db: AsyncSession, active_only: bool = False):
    """获取所有订阅计划"""
    query = select(SubscriptionPlan)
    if active_only:
        query = query.where(SubscriptionPlan.is_active == True)
    result = await db.execute(query)
    return result.scalars().all()


async def get_subscription_plan(db: AsyncSession, plan_id: int):
    """获取单个订阅计划"""
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    return result.scalar_one_or_none()


async def create_order(db: AsyncSession, order: OrderCreate) -> Order:
    """创建订单"""
    db_order = Order(
        user_id=order.user_id,
        plan_id=order.plan_id,
        payment_method=order.payment_method,
        amount=order.amount,
        description=order.description,
        status=PaymentStatus.PENDING,
        created_at=datetime.now()
    )
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    return db_order


async def get_order(db: AsyncSession, order_id: int):
    """获取订单信息"""
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def get_user_orders(db: AsyncSession, user_id: int):
    """获取用户所有订单"""
    result = await db.execute(select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()))
    return result.scalars().all()


async def update_order_status(db: AsyncSession, order_id: int, status: PaymentStatus, transaction_id: str = None):
    """更新订单状态"""
    update_data = {"status": status}
    if status == PaymentStatus.PAID:
        update_data["paid_at"] = datetime.now()
    if transaction_id:
        update_data["transaction_id"] = transaction_id
    
    await db.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(**update_data)
    )
    await db.commit()
    
    # 如果订单已支付，创建或更新用户订阅
    if status == PaymentStatus.PAID:
        order = await get_order(db, order_id)
        if order:
            await create_or_update_user_subscription(db, order)


async def create_or_update_user_subscription(db: AsyncSession, order: Order):
    """创建或更新用户订阅"""
    # 获取订阅计划
    plan = await get_subscription_plan(db, order.plan_id)
    if not plan:
        return None
    
    # 查找用户当前订阅
    result = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == order.user_id, UserSubscription.is_active == True)
    )
    current_subscription = result.scalar_one_or_none()
    
    now = datetime.now()
    end_date = now + timedelta(days=plan.duration_days)
    
    # 如果存在当前订阅，延长结束日期
    if current_subscription:
        # 如果当前订阅已过期，从现在开始计算
        if current_subscription.end_date < now:
            current_subscription.end_date = end_date
        else:
            # 否则在当前结束日期基础上延长
            current_subscription.end_date = current_subscription.end_date + timedelta(days=plan.duration_days)
        
        # 更新数据限制（如果新计划有限制）
        if plan.data_limit_gb:
            current_subscription.data_limit_gb = plan.data_limit_gb
        
        await db.commit()
        return current_subscription
    
    # 创建新订阅
    new_subscription = UserSubscription(
        user_id=order.user_id,
        plan_id=order.plan_id,
        start_date=now,
        end_date=end_date,
        is_active=True,
        data_limit_gb=plan.data_limit_gb,
        data_used_gb=0
    )
    db.add(new_subscription)
    await db.commit()
    await db.refresh(new_subscription)
    
    # 更新用户状态为活跃
    await db.execute(
        update(User)
        .where(User.id == order.user_id)
        .values(status="active")
    )
    await db.commit()
    
    return new_subscription


async def get_user_subscription(db: AsyncSession, user_id: int):
    """获取用户当前订阅"""
    result = await db.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == user_id, UserSubscription.is_active == True)
        .options(selectinload(UserSubscription.plan))
    )
    return result.scalar_one_or_none()


async def update_subscription_usage(db: AsyncSession, user_id: int, used_gb: float):
    """更新用户订阅使用量"""
    subscription = await get_user_subscription(db, user_id)
    if subscription:
        subscription.data_used_gb = used_gb
        
        # 如果超出限制，停用订阅
        if subscription.data_limit_gb and used_gb >= subscription.data_limit_gb:
            subscription.is_active = False
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(status="limited")
            )
        
        await db.commit()
        return subscription
    return None
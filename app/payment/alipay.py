import json
from datetime import datetime, timedelta
from typing import Dict, Any
from urllib.parse import parse_qs

from fastapi import Request
from alipay.aio import AliPay
from app.config import ALIPAY_APP_ID, ALIPAY_PRIVATE_KEY, ALIPAY_PUBLIC_KEY, ALIPAY_NOTIFY_URL, ALIPAY_RETURN_URL, DOMAIN

from app.db.models import Order
from app.payment.base import PaymentProvider


class AlipayProvider(PaymentProvider):
    """支付宝支付提供商"""
    
    def __init__(self):
        self.client = AliPay(
            appid=ALIPAY_APP_ID,
            app_notify_url=ALIPAY_NOTIFY_URL,
            app_private_key_string=ALIPAY_PRIVATE_KEY,
            alipay_public_key_string=ALIPAY_PUBLIC_KEY,
            sign_type="RSA2",
            debug=False  # 生产环境设置为False
        )
    
    async def create_payment(self, order: Order) -> Dict[str, Any]:
        """创建支付宝支付订单"""
        # 订单过期时间为15分钟
        expires_at = datetime.now() + timedelta(minutes=15)
        expires_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")
        
        # 创建支付宝订单
        order_string = self.client.api_alipay_trade_page_pay(
            out_trade_no=str(order.id),
            total_amount=str(order.amount),
            subject=f"Marzban订阅 - {order.description or '套餐购买'}",
            return_url=ALIPAY_RETURN_URL,
            notify_url=ALIPAY_NOTIFY_URL,
            timeout_express="15m"  # 15分钟超时
        )
        
        # 生成支付URL
        payment_url = f"https://openapi.alipay.com/gateway.do?{order_string}"
        
        return {
            "payment_url": payment_url,
            "expires_at": expires_at
        }
    
    async def verify_callback(self, request: Request = None) -> Dict[str, Any]:
        """验证支付宝回调"""
        if not request:
            return {"verified": False}
        
        # 获取回调数据
        if request.headers.get("content-type") == "application/x-www-form-urlencoded":
            data = await request.form()
            params = dict(data)
        else:
            body = await request.body()
            params = parse_qs(body.decode('utf-8'))
            params = {k: v[0] for k, v in params.items()}
        
        # 验证签名
        signature = params.pop("sign", None)
        if not signature:
            return {"verified": False}
        
        success = self.client.verify(params, signature)
        if not success:
            return {"verified": False}
        
        # 检查支付状态
        trade_status = params.get("trade_status")
        if trade_status != "TRADE_SUCCESS":
            return {"verified": False}
        
        # 返回验证结果
        return {
            "verified": True,
            "order_id": int(params.get("out_trade_no")),
            "transaction_id": params.get("trade_no"),
            "amount": float(params.get("total_amount")),
            "paid_at": datetime.now()
        }
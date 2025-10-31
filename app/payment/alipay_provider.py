import asyncio
import time
from typing import Dict, Any, Optional

from alipay.aio import AliPay
from fastapi import HTTPException

from app.payment.base import PaymentProvider
from app.payment.config import (
    ALIPAY_APP_ID,
    ALIPAY_PRIVATE_KEY,
    ALIPAY_PUBLIC_KEY,
    ALIPAY_NOTIFY_URL,
    ALIPAY_RETURN_URL
)


class AlipayProvider(PaymentProvider):
    """支付宝支付提供商实现"""

    def __init__(self):
        """初始化支付宝客户端"""
        if not ALIPAY_APP_ID or not ALIPAY_PRIVATE_KEY or not ALIPAY_PUBLIC_KEY:
            raise ValueError("支付宝配置不完整，请检查环境变量")
        
        self.client = AliPay(
            appid=ALIPAY_APP_ID,
            app_notify_url=ALIPAY_NOTIFY_URL,
            app_private_key_string=ALIPAY_PRIVATE_KEY,
            alipay_public_key_string=ALIPAY_PUBLIC_KEY,
            sign_type="RSA2",
            debug=False
        )

    async def create_payment(self, order_id: str, amount: float, subject: str, description: str) -> Dict[str, Any]:
        """
        创建支付宝支付订单
        
        Args:
            order_id: 订单ID
            amount: 支付金额
            subject: 订单标题
            description: 订单描述
            
        Returns:
            包含支付URL和订单信息的字典
        """
        # 设置订单过期时间为15分钟
        timeout_express = "15m"
        
        # 创建支付宝订单
        order_string = await self.client.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(amount),
            subject=subject,
            return_url=ALIPAY_RETURN_URL,
            notify_url=ALIPAY_NOTIFY_URL,
            body=description,
            timeout_express=timeout_express
        )
        
        # 返回支付URL和订单信息
        return {
            "payment_url": f"{self.client._gateway}?{order_string}",
            "order_id": order_id,
            "amount": amount,
            "expires_at": int(time.time()) + 15 * 60  # 15分钟后过期
        }

    async def verify_callback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证支付宝回调
        
        Args:
            data: 支付宝回调数据
            
        Returns:
            验证后的订单信息
        """
        # 验证签名
        signature_verified = await self.client.verify_async(data)
        if not signature_verified:
            raise HTTPException(status_code=400, detail="支付宝回调签名验证失败")
        
        # 验证交易状态
        trade_status = data.get("trade_status")
        if trade_status != "TRADE_SUCCESS":
            raise HTTPException(status_code=400, detail=f"支付未成功，状态: {trade_status}")
        
        # 返回验证后的订单信息
        return {
            "order_id": data.get("out_trade_no"),
            "transaction_id": data.get("trade_no"),
            "amount": float(data.get("total_amount", 0)),
            "status": "success",
            "paid_at": int(time.time())
        }

    async def query_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单信息，如果订单不存在则返回None
        """
        try:
            result = await self.client.api_alipay_trade_query(out_trade_no=order_id)
            if result.get("code") == "10000":  # 接口调用成功
                trade_status = result.get("trade_status")
                if trade_status == "TRADE_SUCCESS":
                    return {
                        "order_id": order_id,
                        "transaction_id": result.get("trade_no"),
                        "amount": float(result.get("total_amount", 0)),
                        "status": "success",
                        "paid_at": int(time.time())
                    }
                else:
                    return {
                        "order_id": order_id,
                        "status": "pending" if trade_status in ["WAIT_BUYER_PAY"] else "failed",
                        "message": f"订单状态: {trade_status}"
                    }
            return None
        except Exception as e:
            return None
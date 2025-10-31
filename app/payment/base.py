from abc import ABC, abstractmethod
from typing import Dict, Any

from app.db.models import Order


class PaymentProvider(ABC):
    """支付提供商基类"""
    
    @abstractmethod
    async def create_payment(self, order: Order) -> Dict[str, Any]:
        """
        创建支付订单
        
        Args:
            order: 订单对象
            
        Returns:
            Dict: 包含支付URL、二维码等信息的字典
        """
        pass
    
    @abstractmethod
    async def verify_callback(self) -> Dict[str, Any]:
        """
        验证支付回调
        
        Returns:
            Dict: 验证结果，包含订单ID、交易ID等信息
        """
        pass
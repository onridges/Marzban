from app.models.billing import PaymentMethod
from app.payment.alipay import AlipayProvider
from app.payment.base import PaymentProvider


def create_payment_provider(payment_method: PaymentMethod) -> PaymentProvider:
    """
    创建支付提供商实例
    
    Args:
        payment_method: 支付方式
        
    Returns:
        PaymentProvider: 支付提供商实例
    """
    if payment_method == PaymentMethod.ALIPAY:
        return AlipayProvider()
    # 未来可以添加其他支付方式
    # elif payment_method == PaymentMethod.WECHAT:
    #     return WechatPayProvider()
    # elif payment_method == PaymentMethod.STRIPE:
    #     return StripeProvider()
    return None
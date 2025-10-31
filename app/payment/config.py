from decouple import config

# 支付宝配置
DOMAIN = config("DOMAIN", default="http://localhost:8000")
ALIPAY_APP_ID = config("ALIPAY_APP_ID", default="")
ALIPAY_PRIVATE_KEY = config("ALIPAY_PRIVATE_KEY", default="")
ALIPAY_PUBLIC_KEY = config("ALIPAY_PUBLIC_KEY", default="")
ALIPAY_NOTIFY_URL = config("ALIPAY_NOTIFY_URL", default=f"{DOMAIN}/api/v1/payment/callback/alipay")
ALIPAY_RETURN_URL = config("ALIPAY_RETURN_URL", default=f"{DOMAIN}/dashboard/user")

# 微信支付配置（预留）
WECHAT_APP_ID = config("WECHAT_APP_ID", default="")
WECHAT_MCH_ID = config("WECHAT_MCH_ID", default="")
WECHAT_API_KEY = config("WECHAT_API_KEY", default="")
WECHAT_NOTIFY_URL = config("WECHAT_NOTIFY_URL", default=f"{DOMAIN}/api/v1/payment/callback/wechat")

# Stripe配置（预留）
STRIPE_API_KEY = config("STRIPE_API_KEY", default="")
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_RETURN_URL = config("STRIPE_RETURN_URL", default=f"{DOMAIN}/dashboard/user")
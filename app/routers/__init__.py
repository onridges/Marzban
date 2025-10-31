from fastapi import APIRouter
from . import (
    admin, 
    core, 
    node, 
    subscription, 
    system, 
    user_template, 
    user,
    auth,
    home,
    user_center,
)

api_router = APIRouter()

routers = [
    admin.router,
    core.router,
    node.router,
    subscription.router,
    system.router,
    user_template.router,
    auth.router,
    home.router,
    user_center.router,
    user.router,
]

for router in routers:
    api_router.include_router(router)

__all__ = ["api_router"]
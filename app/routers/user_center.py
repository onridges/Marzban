from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db, crud
from app.dependencies import get_current_user, validate_dates
from app.models.user import UserResponse
from app.utils import responses

router = APIRouter(tags=["UserCenter"], prefix="/api/user", responses={401: responses._401})


@router.get("/me", response_model=UserResponse)
def get_me(
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dbuser = crud.get_user(db, username=user.username)
    if not dbuser:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(dbuser)


@router.get("/usage")
def get_my_usage(
    user = Depends(get_current_user),
    start: str = "",
    end: str = "",
    db: Session = Depends(get_db),
):
    start, end = validate_dates(start, end)
    dbuser = crud.get_user(db, username=user.username)
    if not dbuser:
        raise HTTPException(status_code=404, detail="User not found")
    usages = crud.get_user_usages(db, dbuser, start, end)
    return {"usages": usages, "username": dbuser.username}


@router.get("/subscription")
def get_my_subscription(
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 如果有计费模块，可返回当前订阅信息；暂时返回用户对象中的 subscription_url
    dbuser = crud.get_user(db, username=user.username)
    if not dbuser:
        raise HTTPException(status_code=404, detail="User not found")
    return {"subscription_url": UserResponse.model_validate(dbuser).subscription_url}


@router.get("/packages")
def get_my_packages(
    user = Depends(get_current_user),
):
    # 预留：如有套餐/包信息，可在此返回；暂时返回空列表
    return []
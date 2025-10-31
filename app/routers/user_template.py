from typing import List
from datetime import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy.exc import IntegrityError
from fastapi import Depends, HTTPException, APIRouter

from app.db import Session, crud, get_db
from app.models.admin import Admin
from app.models.user import UserModify, UserResponse, UserStatus
from app.models.user_template import (
    UserTemplateCreate,
    UserTemplateModify,
    UserTemplateResponse,
    ApplyTemplateRequest,
    ApplyTemplateResult,
)
from app.dependencies import get_user_template
from app import xray


router = APIRouter(tags=["User Template"], prefix="/api")


@router.post("/user_template", response_model=UserTemplateResponse)
def add_user_template(
    new_user_template: UserTemplateCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.check_sudo_admin),
):
    """
    Add a new user template

    - **name** can be up to 64 characters
    - **data_limit** must be in bytes and larger or equal to 0
    - **expire_duration** must be in seconds and larger or equat to 0
    - **inbounds** dictionary of protocol:inbound_tags, empty means all inbounds
    """
    try:
        return crud.create_user_template(db, new_user_template)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Template by this name already exists")


@router.get("/user_template/{template_id}", response_model=UserTemplateResponse)
def get_user_template_endpoint(
    dbuser_template: UserTemplateResponse = Depends(get_user_template),
    admin: Admin = Depends(Admin.get_current),
):
    """Get User Template information with id"""
    return dbuser_template


@router.put("/user_template/{template_id}", response_model=UserTemplateResponse)
def modify_user_template(
    modify_user_template: UserTemplateModify,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.check_sudo_admin),
    dbuser_template: UserTemplateResponse = Depends(get_user_template),
):
    """
    Modify User Template

    - **name** can be up to 64 characters
    - **data_limit** must be in bytes and larger or equal to 0
    - **expire_duration** must be in seconds and larger or equat to 0
    - **inbounds** dictionary of protocol:inbound_tags, empty means all inbounds
    """
    try:
        return crud.update_user_template(db, dbuser_template, modify_user_template)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Template by this name already exists")


@router.delete("/user_template/{template_id}")
def remove_user_template(
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.check_sudo_admin),
    dbuser_template: UserTemplateResponse = Depends(get_user_template),
):
    """Remove a User Template by its ID"""
    return crud.remove_user_template(db, dbuser_template)


@router.get("/user_template", response_model=List[UserTemplateResponse])
def get_user_templates(
    offset: int = None,
    limit: int = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.get_current),
):
    """Get a list of User Templates with optional pagination"""
    return crud.get_user_templates(db, offset, limit)


@router.post("/user_template/apply", response_model=ApplyTemplateResult)
def apply_template_bulk(
    payload: ApplyTemplateRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Apply a template to selected users in bulk."""
    updated: List[str] = []
    not_found: List[str] = []

    template_db = crud.get_user_template(db, payload.template_id)
    if not template_db:
        raise HTTPException(status_code=404, detail="Template not found")
    template = UserTemplateResponse.model_validate(template_db)

    # Compute base expire date (end of today) + template duration if requested
    today = datetime.now()
    base_today = datetime(
        year=today.year,
        month=today.month,
        day=today.day,
        hour=23,
        minute=59,
        second=59,
    )

    for username in payload.usernames:
        db_user = crud.get_user(db, username)
        if not db_user:
            not_found.append(username)
            continue

        modify_kwargs = {}
        if payload.apply_inbounds:
            modify_kwargs["inbounds"] = template.inbounds or {}
        if payload.apply_data_limit:
            modify_kwargs["data_limit"] = template.data_limit
        if payload.apply_expire_duration:
            expire_date = None
            if template.expire_duration:
                expire_date = base_today + relativedelta(seconds=template.expire_duration)
            modify_kwargs["expire"] = int(expire_date.timestamp()) if expire_date else 0

        try:
            db_user = crud.update_user(db, db_user, UserModify(**modify_kwargs))
            # Update xray runtime if user is active
            user = UserResponse.model_validate(db_user)
            if user.status == UserStatus.active:
                xray.operations.update_user(db_user)
            updated.append(username)
        except Exception:
            not_found.append(username)

    return ApplyTemplateResult(updated=updated, not_found=not_found)
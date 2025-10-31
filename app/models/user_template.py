from typing import List

from pydantic import BaseModel

from app.models.user_template_base import (
    UserTemplate,
    UserTemplateCreate,
    UserTemplateModify,
    UserTemplateResponse,
)


class ApplyTemplateRequest(BaseModel):
    template_id: int
    usernames: List[str]
    apply_inbounds: bool = True
    apply_data_limit: bool = True
    apply_expire_duration: bool = True


class ApplyTemplateResult(BaseModel):
    updated: List[str]
    not_found: List[str]
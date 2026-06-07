# -*- coding: utf-8 -*-
"""
管理员用户管理 Pydantic 模型

公开接口：
- AdminUserOut
- AdminUserUpdate
"""

from datetime import datetime
from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field

from src.server.auth.schemas import UserRole, UserStatus
from src.server.project_management.schemas import ProjectSummary


class AdminUserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    name: Optional[str] = Field(default=None)
    wechat_nickname: Optional[str] = Field(default=None)
    wechat_id: Optional[str] = Field(default=None)
    role: UserRole
    status: UserStatus
    scope_overrides: list[str] | None = Field(
        default=None,
        validation_alias=AliasChoices("scope_overrides_list"),
    )
    effective_scopes: list[str]
    available_scopes: list[str]
    projects: list[ProjectSummary] = Field(
        default_factory=list,
        validation_alias=AliasChoices("project_summaries", "projects"),
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    name: Optional[str] = Field(default=None, max_length=100)
    wechat_nickname: Optional[str] = Field(default=None, max_length=100)
    wechat_id: Optional[str] = Field(default=None, max_length=100)
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    password: str = Field(..., min_length=8)
    project_ids: list[int] = Field(default_factory=list)


class AdminUserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(default=None, max_length=100)
    wechat_nickname: Optional[str] = Field(default=None, max_length=100)
    wechat_id: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    password: Optional[str] = Field(default=None, min_length=8)
    project_ids: Optional[list[int]] = None


class AdminUserScopesUpdate(BaseModel):
    scopes: list[str] = Field(default_factory=list)

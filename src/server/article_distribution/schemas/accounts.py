# -*- coding: utf-8 -*-
"""Account schemas for article distribution."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .types import PublicationType

class AccountCreate(BaseModel):
    account_name: str = Field(..., min_length=1, max_length=120)
    platform: str = Field(..., min_length=1, max_length=80)
    publication_type: PublicationType
    is_active: bool = True
    user_id: int | None = Field(default=None, ge=1)


class AccountUpdate(BaseModel):
    account_name: str | None = Field(default=None, min_length=1, max_length=120)
    platform: str | None = Field(default=None, min_length=1, max_length=80)
    publication_type: PublicationType | None = None
    is_active: bool | None = None
    user_id: int | None = Field(default=None, ge=1)


class AccountOut(BaseModel):
    id: int
    user_id: int
    account_name: str
    platform: str
    publication_type: PublicationType
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountPageOut(BaseModel):
    items: list[AccountOut]
    total: int
    page: int
    page_size: int


class AccountDirectoryOut(BaseModel):
    id: int
    platform: str
    account_name: str
    publication_type: PublicationType
    is_active: bool


class UserAccountDirectoryOut(BaseModel):
    id: int
    name: str
    accounts: list[AccountDirectoryOut]

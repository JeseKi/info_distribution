# -*- coding: utf-8 -*-
"""Article distribution Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PublicationType = Literal["video", "article", "image_text"]
PublishStatus = Literal["unpublished", "published"]


class AccountCreate(BaseModel):
    account_name: str = Field(..., min_length=1, max_length=120)
    platform: str = Field(..., min_length=1, max_length=80)
    publication_type: PublicationType
    user_id: int | None = Field(default=None, ge=1)


class AccountUpdate(BaseModel):
    account_name: str | None = Field(default=None, min_length=1, max_length=120)
    platform: str | None = Field(default=None, min_length=1, max_length=80)
    publication_type: PublicationType | None = None
    user_id: int | None = Field(default=None, ge=1)


class AccountOut(BaseModel):
    id: int
    user_id: int
    account_name: str
    platform: str
    publication_type: PublicationType
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleUploadItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    markdown_content: str = Field(..., min_length=1)
    scheduled_date: date


class ArticleBatchCreate(BaseModel):
    account_id: int = Field(..., ge=1)
    articles: list[ArticleUploadItem] = Field(..., min_length=1, max_length=100)


class ArticleStatusUpdate(BaseModel):
    publish_status: PublishStatus


class ArticleOut(BaseModel):
    id: int
    user_id: int
    account_id: int
    title: str
    markdown_content: str
    scheduled_date: date
    publish_status: PublishStatus
    source: str
    created_by_user_id: int | None
    api_key_id: int | None
    created_at: datetime
    updated_at: datetime
    account: AccountOut | None = None

    model_config = ConfigDict(from_attributes=True)


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class APIKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str
    created_by_user_id: int
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class APIKeyCreateOut(APIKeyOut):
    api_key: str

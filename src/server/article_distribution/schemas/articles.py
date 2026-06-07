# -*- coding: utf-8 -*-
"""Article schemas for article distribution."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.server.project_management.schemas import ProjectSummary

from .accounts import AccountOut
from .types import PublishStatus

class ArticleUploadItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    markdown_content: str = Field(..., min_length=1)
    scheduled_date: date
    project_id: int = Field(..., ge=1)
    metadata: dict[str, Any] | None = None


class ArticleBatchCreate(BaseModel):
    account_id: int = Field(..., ge=1)
    articles: list[ArticleUploadItem] = Field(..., min_length=1, max_length=100)


class ArticleStatusUpdate(BaseModel):
    publish_status: PublishStatus
    published_url: str | None = Field(default=None, max_length=2048)


class ArticleUpdate(BaseModel):
    account_id: int | None = Field(default=None, ge=1)
    project_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    markdown_content: str | None = Field(default=None, min_length=1)
    scheduled_date: date | None = None
    publish_status: PublishStatus | None = None
    published_url: str | None = Field(default=None, max_length=2048)
    metadata: dict[str, Any] | None = None


class ArticleV1Update(BaseModel):
    account_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, max_length=200)
    markdown_content: str | None = None
    scheduled_date: date | None = None
    publish_status: PublishStatus | None = None
    published_url: str | None = Field(default=None, max_length=2048)
    metadata: dict[str, Any] | None = None


class ArticleV2Update(BaseModel):
    account_id: int | None = Field(default=None, ge=1)
    project_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, max_length=200)
    markdown_content: str | None = None
    scheduled_date: date | None = None
    publish_status: PublishStatus | None = None
    published_url: str | None = Field(default=None, max_length=2048)
    metadata: dict[str, Any] | None = None


class ArticleOut(BaseModel):
    id: int
    user_id: int
    account_id: int
    project_id: int
    title: str
    markdown_content: str
    metadata: dict[str, Any] | None = None
    scheduled_date: date
    publish_status: PublishStatus
    published_url: str | None
    source: str
    created_by_user_id: int | None
    api_key_id: int | None
    created_at: datetime
    updated_at: datetime
    account: AccountOut | None = None
    project: ProjectSummary | None = None

    model_config = ConfigDict(from_attributes=True)


class ArticleStatusCountsOut(BaseModel):
    unpublished: int = 0
    published: int = 0
    invalid: int = 0


class ArticlePageOut(BaseModel):
    items: list[ArticleOut]
    total: int
    page: int
    page_size: int
    status_counts: ArticleStatusCountsOut

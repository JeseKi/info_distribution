# -*- coding: utf-8 -*-
"""Overview report schemas for article distribution."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .reports_unpublished import ArticleDistributionPlatformSummaryOut
from .traffic import ArticleTrafficStatOut
from .types import ArticleDistributionOverviewView, PublicationType, PublishStatus

class ArticleDistributionOverviewSummaryOut(BaseModel):
    total_users: int = 0
    total_articles: int = 0
    published_articles: int = 0
    unpublished_articles: int = 0
    invalid_articles: int = 0
    inactive_account_articles: int = 0
    missing_articles: int = 0
    topic_count: int = 0
    material_count: int = 0
    read_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    share_count: int = 0


class ArticleDistributionOverviewArticleOut(BaseModel):
    item_type: Literal["article"] = "article"
    id: int
    title: str
    scheduled_date: date
    user_id: int
    username: str
    name: str | None
    email: str
    account_id: int
    account_name: str
    platform: str
    publication_type: PublicationType
    account_is_active: bool
    publish_status: PublishStatus
    published_url: str | None
    created_at: datetime
    missing_traffic: bool = False
    output_id: str | None = None
    topic: str | None = None
    materials: list[str] = Field(default_factory=list)
    article_role: str | None = None
    angle_label: str | None = None
    audience_label: str | None = None
    latest_traffic_stat: ArticleTrafficStatOut | None = None


class ArticleDistributionOverviewArticleDetailOut(ArticleDistributionOverviewArticleOut):
    markdown_content: str
    summary: str | None = None
    metadata: dict[str, Any] | None = None


class ArticleDistributionOverviewUserOut(BaseModel):
    item_type: Literal["user"] = "user"
    user_id: int
    username: str
    name: str | None
    email: str
    remaining_count: int = 0
    published_count: int = 0
    invalid_count: int = 0
    inactive_account_articles: int = 0
    missing_count: int = 0
    read_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    share_count: int = 0
    platform_summaries: list[ArticleDistributionPlatformSummaryOut]
    articles: list[ArticleDistributionOverviewArticleOut]


class ArticleDistributionOverviewTopicOut(BaseModel):
    item_type: Literal["topic"] = "topic"
    key: str
    output_id: str | None = None
    topic: str
    materials: list[str]
    article_count: int
    read_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    share_count: int = 0
    articles: list[ArticleDistributionOverviewArticleOut]


class ArticleDistributionOverviewOut(BaseModel):
    view: ArticleDistributionOverviewView
    summary: ArticleDistributionOverviewSummaryOut
    items: list[
        ArticleDistributionOverviewUserOut
        | ArticleDistributionOverviewArticleOut
        | ArticleDistributionOverviewTopicOut
    ]
    total: int
    page: int
    page_size: int


class ArticleDistributionOverviewArticlePageOut(BaseModel):
    items: list[ArticleDistributionOverviewArticleOut]
    total: int
    page: int
    page_size: int

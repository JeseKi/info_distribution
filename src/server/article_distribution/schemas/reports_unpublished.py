# -*- coding: utf-8 -*-
"""Unpublished report schemas for article distribution."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from .traffic import ArticleTrafficStatOut
from .types import PublicationType, PublishStatus

class ArticleDistributionPendingArticleOut(BaseModel):
    id: int
    title: str
    markdown_content: str
    scheduled_date: date
    account_id: int
    account_name: str
    platform: str
    publication_type: PublicationType
    account_is_active: bool
    publish_status: PublishStatus
    published_url: str | None
    created_at: datetime
    latest_traffic_stat: ArticleTrafficStatOut | None = None


class ArticleDistributionPlatformSummaryOut(BaseModel):
    account_id: int
    account_name: str
    platform: str
    publication_type: PublicationType
    account_is_active: bool
    published_count: int
    unpublished_count: int
    invalid_count: int
    latest_published_url: str | None = None


class ArticleDistributionPendingUserOut(BaseModel):
    user_id: int
    username: str
    name: str | None
    email: str
    remaining_count: int
    published_count: int
    invalid_count: int
    inactive_account_articles: int = 0
    read_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    share_count: int = 0
    platform_summaries: list[ArticleDistributionPlatformSummaryOut]
    articles: list[ArticleDistributionPendingArticleOut]


class ArticleDistributionReportSummaryOut(BaseModel):
    total_users: int
    unpublished_users: int
    published_articles: int
    unpublished_articles: int
    invalid_articles: int
    inactive_account_articles: int
    read_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    share_count: int = 0


class ArticleDistributionReportOut(BaseModel):
    summary: ArticleDistributionReportSummaryOut
    users: list[ArticleDistributionPendingUserOut]

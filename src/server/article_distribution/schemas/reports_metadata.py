# -*- coding: utf-8 -*-
"""Metadata dashboard report schemas for article distribution."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel

from .traffic import ArticleTrafficStatOut
from .types import PublicationType, PublishStatus

class ArticleDistributionMetadataDashboardArticleOut(BaseModel):
    id: int
    title: str
    markdown_content: str
    scheduled_date: date
    publish_status: PublishStatus
    published_url: str | None
    account_id: int
    account_name: str
    platform: str
    publication_type: PublicationType
    account_is_active: bool
    article_role: str | None = None
    angle_label: str | None = None
    audience_label: str | None = None
    summary: str | None = None
    metadata: dict[str, Any] | None = None
    latest_traffic_stat: ArticleTrafficStatOut | None = None


class ArticleDistributionMetadataDashboardTopicOut(BaseModel):
    key: str
    output_id: str | None = None
    topic: str
    materials: list[str]
    article_count: int
    read_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    share_count: int = 0
    articles: list[ArticleDistributionMetadataDashboardArticleOut]


class ArticleDistributionMetadataDashboardSummaryOut(BaseModel):
    topic_count: int
    article_count: int
    material_count: int
    read_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    share_count: int = 0


class ArticleDistributionMetadataDashboardOut(BaseModel):
    summary: ArticleDistributionMetadataDashboardSummaryOut
    topics: list[ArticleDistributionMetadataDashboardTopicOut]
    total: int
    page: int
    page_size: int

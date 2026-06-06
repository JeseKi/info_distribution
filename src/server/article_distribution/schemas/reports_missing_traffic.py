# -*- coding: utf-8 -*-
"""Missing traffic report schemas for article distribution."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from .traffic import ArticleTrafficStatOut
from .types import PublicationType

class ArticleDistributionMissingTrafficArticleOut(BaseModel):
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
    published_url: str
    latest_traffic_stat: ArticleTrafficStatOut | None = None


class ArticleDistributionMissingTrafficPageOut(BaseModel):
    items: list[ArticleDistributionMissingTrafficArticleOut]
    total: int
    page: int
    page_size: int


class ArticleDistributionMissingTrafficUserOut(BaseModel):
    user_id: int
    username: str
    name: str | None
    email: str
    missing_count: int
    read_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    share_count: int = 0
    articles: list[ArticleDistributionMissingTrafficArticleOut]


class ArticleDistributionMissingTrafficSummaryOut(BaseModel):
    total_users: int
    missing_articles: int
    read_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    share_count: int = 0


class ArticleDistributionMissingTrafficReportOut(BaseModel):
    summary: ArticleDistributionMissingTrafficSummaryOut
    users: list[ArticleDistributionMissingTrafficUserOut]

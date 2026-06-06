# -*- coding: utf-8 -*-
"""Public dashboard report schemas for article distribution."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from .reports_unpublished import ArticleDistributionReportSummaryOut
from .traffic import ArticleTrafficStatOut
from .types import PublicationType

class ArticleDistributionPublicArticleOut(BaseModel):
    id: int
    title: str
    published_at: date
    published_url: str
    account_name: str
    platform: str
    publication_type: PublicationType
    latest_traffic_stat: ArticleTrafficStatOut | None = None


class ArticleDistributionPublicDashboardOut(BaseModel):
    summary: ArticleDistributionReportSummaryOut
    articles: list[ArticleDistributionPublicArticleOut]
    total: int
    page: int
    page_size: int

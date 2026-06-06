# -*- coding: utf-8 -*-
"""Traffic statistic schemas for article distribution."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .articles import ArticleOut

class ArticleTrafficStatCreate(BaseModel):
    read_count: int = Field(default=0, ge=0)
    like_count: int = Field(default=0, ge=0)
    favorite_count: int = Field(default=0, ge=0)
    share_count: int = Field(default=0, ge=0)
    recorded_at: datetime | None = None


class ArticleTrafficStatOut(BaseModel):
    id: int
    user_id: int
    account_id: int
    article_id: int
    read_count: int
    like_count: int
    favorite_count: int
    share_count: int
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleTrafficSummaryOut(BaseModel):
    article: ArticleOut
    latest_stat: ArticleTrafficStatOut | None = None
    record_count: int = 0


class ArticleTrafficSummaryPageOut(BaseModel):
    items: list[ArticleTrafficSummaryOut]
    total: int
    page: int
    page_size: int

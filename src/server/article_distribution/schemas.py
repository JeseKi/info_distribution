# -*- coding: utf-8 -*-
"""Article distribution Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PublicationType = Literal["video", "article", "image_text"]
PublishStatus = Literal["unpublished", "published", "invalid"]
AccountStatusFilter = Literal["active", "inactive", "all"]
ArticleDistributionOverviewView = Literal["users", "articles", "topics"]


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


class ArticleUploadItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    markdown_content: str = Field(..., min_length=1)
    scheduled_date: date
    metadata: dict[str, Any] | None = None


class ArticleBatchCreate(BaseModel):
    account_id: int = Field(..., ge=1)
    articles: list[ArticleUploadItem] = Field(..., min_length=1, max_length=100)


class ArticleStatusUpdate(BaseModel):
    publish_status: PublishStatus
    published_url: str | None = Field(default=None, max_length=2048)


class ArticleUpdate(BaseModel):
    account_id: int | None = Field(default=None, ge=1)
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


class ArticleOut(BaseModel):
    id: int
    user_id: int
    account_id: int
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
    markdown_content: str
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
    summary: str | None = None
    metadata: dict[str, Any] | None = None
    latest_traffic_stat: ArticleTrafficStatOut | None = None


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

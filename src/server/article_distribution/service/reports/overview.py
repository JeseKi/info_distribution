# -*- coding: utf-8 -*-
"""Overview report service."""

from __future__ import annotations

from datetime import date, datetime
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ...dao import ArticleDistributionDAO
from ...schemas import (
    AccountStatusFilter,
    ArticleDistributionOverviewArticleDetailOut,
    ArticleDistributionOverviewArticlePageOut,
    ArticleDistributionOverviewOut,
    ArticleDistributionOverviewView,
)
from ..helpers import normalize_optional
from .common import _normalize_datetime
from .overview_builders import (
    _overview_articles_from_rows,
    _overview_summary,
    _overview_topics_from_articles,
    _overview_users_from_articles,
)
from .types import OverviewItemOut

def list_report_overview(
    db: Session,
    *,
    view: ArticleDistributionOverviewView = "users",
    keyword: str | None = None,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "active",
    publish_status: str | None = None,
    missing_traffic_only: bool = False,
    recorded_from: datetime | None = None,
    recorded_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ArticleDistributionOverviewOut:
    normalized_recorded_from: datetime | None = None
    normalized_recorded_to: datetime | None = None
    if recorded_from is not None and recorded_to is not None:
        normalized_recorded_from = _normalize_datetime(recorded_from)
        normalized_recorded_to = _normalize_datetime(recorded_to)
        if normalized_recorded_from >= normalized_recorded_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="流量统计时间范围无效",
            )
    elif missing_traffic_only:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="筛选未填流量时必须提供流量统计时间范围",
        )

    dao = ArticleDistributionDAO(db)
    normalized_keyword = normalize_optional(keyword)
    normalized_platform = normalize_optional(platform)

    all_rows = dao.list_overview_article_owner_rows(
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        platform=normalized_platform,
        publication_type=publication_type,
        account_status=account_status,
        publish_status=publish_status,
        keyword=normalized_keyword,
        missing_traffic_only=missing_traffic_only,
        recorded_from=normalized_recorded_from,
        recorded_to=normalized_recorded_to,
    )
    all_articles = _overview_articles_from_rows(
        db,
        all_rows,
        recorded_from=normalized_recorded_from,
        recorded_to=normalized_recorded_to,
    )
    summary = _overview_summary(all_articles)

    if view == "articles":
        page_rows, total = dao.list_overview_article_owner_rows_page(
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=normalized_platform,
            publication_type=publication_type,
            account_status=account_status,
            publish_status=publish_status,
            keyword=normalized_keyword,
            missing_traffic_only=missing_traffic_only,
            recorded_from=normalized_recorded_from,
            recorded_to=normalized_recorded_to,
            page=page,
            page_size=page_size,
        )
        article_items = cast(
            list[OverviewItemOut],
            _overview_articles_from_rows(
                db,
                page_rows,
                recorded_from=normalized_recorded_from,
                recorded_to=normalized_recorded_to,
            ),
        )
        return ArticleDistributionOverviewOut(
            view=view,
            summary=summary,
            items=article_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    if view == "topics":
        topics = _overview_topics_from_articles(all_articles, include_articles=False)
        paged_topics = cast(
            list[OverviewItemOut],
            topics[(page - 1) * page_size : page * page_size],
        )
        return ArticleDistributionOverviewOut(
            view=view,
            summary=summary,
            items=paged_topics,
            total=len(topics),
            page=page,
            page_size=page_size,
        )

    users = _overview_users_from_articles(all_articles, include_articles=False)
    paged_users = cast(
        list[OverviewItemOut],
        users[(page - 1) * page_size : page * page_size],
    )
    return ArticleDistributionOverviewOut(
        view=view,
        summary=summary,
        items=paged_users,
        total=len(users),
        page=page,
        page_size=page_size,
    )


def list_report_overview_articles(
    db: Session,
    *,
    user_id: int | None = None,
    topic_key: str | None = None,
    keyword: str | None = None,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "active",
    publish_status: str | None = None,
    missing_traffic_only: bool = False,
    recorded_from: datetime | None = None,
    recorded_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ArticleDistributionOverviewArticlePageOut:
    normalized_recorded_from: datetime | None = None
    normalized_recorded_to: datetime | None = None
    if recorded_from is not None and recorded_to is not None:
        normalized_recorded_from = _normalize_datetime(recorded_from)
        normalized_recorded_to = _normalize_datetime(recorded_to)
        if normalized_recorded_from >= normalized_recorded_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="流量统计时间范围无效",
            )
    elif missing_traffic_only:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="筛选未填流量时必须提供流量统计时间范围",
        )

    dao = ArticleDistributionDAO(db)
    page_rows, total = dao.list_overview_article_owner_rows_page(
        user_id=user_id,
        topic_key=normalize_optional(topic_key),
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        account_status=account_status,
        publish_status=publish_status,
        keyword=normalize_optional(keyword),
        missing_traffic_only=missing_traffic_only,
        recorded_from=normalized_recorded_from,
        recorded_to=normalized_recorded_to,
        page=page,
        page_size=page_size,
    )
    return ArticleDistributionOverviewArticlePageOut(
        items=_overview_articles_from_rows(
            db,
            page_rows,
            recorded_from=normalized_recorded_from,
            recorded_to=normalized_recorded_to,
        ),
        total=total,
        page=page,
        page_size=page_size,
    )


def get_report_overview_article_detail(
    db: Session,
    *,
    article_id: int,
    recorded_from: datetime | None = None,
    recorded_to: datetime | None = None,
) -> ArticleDistributionOverviewArticleDetailOut:
    normalized_recorded_from: datetime | None = None
    normalized_recorded_to: datetime | None = None
    if recorded_from is not None and recorded_to is not None:
        normalized_recorded_from = _normalize_datetime(recorded_from)
        normalized_recorded_to = _normalize_datetime(recorded_to)
        if normalized_recorded_from >= normalized_recorded_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="流量统计时间范围无效",
            )

    row = ArticleDistributionDAO(db).get_overview_article_owner_row(article_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在",
        )
    articles = _overview_articles_from_rows(
        db,
        [row],
        recorded_from=normalized_recorded_from,
        recorded_to=normalized_recorded_to,
        include_detail_fields=True,
    )
    return cast(ArticleDistributionOverviewArticleDetailOut, articles[0])

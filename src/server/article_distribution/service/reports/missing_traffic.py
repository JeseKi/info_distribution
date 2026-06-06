# -*- coding: utf-8 -*-
"""Missing traffic report service."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ...dao import ArticleDistributionDAO
from ...schemas import (
    AccountStatusFilter,
    ArticleDistributionMissingTrafficArticleOut,
    ArticleDistributionMissingTrafficPageOut,
    ArticleDistributionMissingTrafficReportOut,
    ArticleDistributionMissingTrafficSummaryOut,
    ArticleDistributionMissingTrafficUserOut,
    ArticleTrafficStatOut,
)
from ..helpers import normalize_optional, normalize_publication_type
from .common import _normalize_datetime, _recent_scheduled_from

def list_missing_traffic_articles(
    db: Session,
    *,
    recorded_from: datetime,
    recorded_to: datetime,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "active",
    page: int = 1,
    page_size: int = 10,
) -> ArticleDistributionMissingTrafficPageOut:
    normalized_recorded_from = _normalize_datetime(recorded_from)
    normalized_recorded_to = _normalize_datetime(recorded_to)
    if normalized_recorded_from >= normalized_recorded_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="流量统计时间范围无效",
        )
    effective_scheduled_from = _recent_scheduled_from(
        scheduled_from, normalized_recorded_to
    )

    dao = ArticleDistributionDAO(db)
    rows, total = dao.list_missing_traffic_article_rows_page(
        recorded_from=normalized_recorded_from,
        recorded_to=normalized_recorded_to,
        scheduled_from=effective_scheduled_from,
        scheduled_to=scheduled_to,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        account_status=account_status,
        page=page,
        page_size=page_size,
    )
    latest_traffic_stats = dao.latest_traffic_stats_by_article_ids(
        [article.id for article, _, _ in rows]
    )
    return ArticleDistributionMissingTrafficPageOut(
        items=[
            ArticleDistributionMissingTrafficArticleOut(
                id=article.id,
                title=article.title,
                scheduled_date=article.scheduled_date,
                user_id=owner.id,
                username=owner.username,
                name=owner.name,
                email=owner.email,
                account_id=account.id,
                account_name=account.account_name,
                platform=account.platform,
                publication_type=normalize_publication_type(account.publication_type),
                account_is_active=account.is_active,
                published_url=article.published_url or "",
                latest_traffic_stat=(
                    ArticleTrafficStatOut.model_validate(latest_traffic_stats[article.id])
                    if article.id in latest_traffic_stats
                    else None
                ),
            )
            for article, account, owner in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


def list_missing_traffic_report(
    db: Session,
    *,
    recorded_from: datetime,
    recorded_to: datetime,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "active",
) -> ArticleDistributionMissingTrafficReportOut:
    rows = _list_missing_traffic_rows(
        db,
        recorded_from=recorded_from,
        recorded_to=recorded_to,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        platform=platform,
        publication_type=publication_type,
        account_status=account_status,
    )
    users = _build_missing_traffic_user_reports(db, rows, include_articles=False)
    return ArticleDistributionMissingTrafficReportOut(
        summary=ArticleDistributionMissingTrafficSummaryOut(
            total_users=len(users),
            missing_articles=sum(user.missing_count for user in users),
            read_count=sum(user.read_count for user in users),
            like_count=sum(user.like_count for user in users),
            favorite_count=sum(user.favorite_count for user in users),
            share_count=sum(user.share_count for user in users),
        ),
        users=users,
    )


def get_missing_traffic_report_user_detail(
    db: Session,
    *,
    user_id: int,
    recorded_from: datetime,
    recorded_to: datetime,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "active",
) -> ArticleDistributionMissingTrafficUserOut:
    rows = _list_missing_traffic_rows(
        db,
        user_id=user_id,
        recorded_from=recorded_from,
        recorded_to=recorded_to,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        platform=platform,
        publication_type=publication_type,
        account_status=account_status,
    )
    users = _build_missing_traffic_user_reports(db, rows, include_articles=True)
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户无匹配文章")
    return users[0]


def _list_missing_traffic_rows(
    db: Session,
    *,
    recorded_from: datetime,
    recorded_to: datetime,
    user_id: int | None = None,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "active",
) -> list[tuple]:
    normalized_recorded_from = _normalize_datetime(recorded_from)
    normalized_recorded_to = _normalize_datetime(recorded_to)
    if normalized_recorded_from >= normalized_recorded_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="流量统计时间范围无效",
        )
    effective_scheduled_from = _recent_scheduled_from(
        scheduled_from, normalized_recorded_to
    )
    return ArticleDistributionDAO(db).list_missing_traffic_article_owner_rows(
        recorded_from=normalized_recorded_from,
        recorded_to=normalized_recorded_to,
        user_id=user_id,
        scheduled_from=effective_scheduled_from,
        scheduled_to=scheduled_to,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        account_status=account_status,
    )


def _build_missing_traffic_user_reports(
    db: Session,
    rows: list[tuple],
    *,
    include_articles: bool,
) -> list[ArticleDistributionMissingTrafficUserOut]:
    grouped: dict[int, ArticleDistributionMissingTrafficUserOut] = {}
    latest_traffic_stats = ArticleDistributionDAO(db).latest_traffic_stats_by_article_ids(
        [article.id for article, _, _ in rows]
    )
    for article, account, owner in rows:
        if owner.id not in grouped:
            grouped[owner.id] = ArticleDistributionMissingTrafficUserOut(
                user_id=owner.id,
                username=owner.username,
                name=owner.name,
                email=owner.email,
                missing_count=0,
                read_count=0,
                like_count=0,
                favorite_count=0,
                share_count=0,
                articles=[],
            )
        latest_stat = latest_traffic_stats.get(article.id)
        user_report = grouped[owner.id]
        user_report.missing_count += 1
        if latest_stat is not None:
            user_report.read_count += latest_stat.read_count
            user_report.like_count += latest_stat.like_count
            user_report.favorite_count += latest_stat.favorite_count
            user_report.share_count += latest_stat.share_count
        if include_articles:
            user_report.articles.append(
                _missing_traffic_article_out(article, account, owner, latest_stat)
            )
    return list(grouped.values())


def _missing_traffic_article_out(
    article,
    account,
    owner,
    latest_stat,
) -> ArticleDistributionMissingTrafficArticleOut:
    return ArticleDistributionMissingTrafficArticleOut(
        id=article.id,
        title=article.title,
        scheduled_date=article.scheduled_date,
        user_id=owner.id,
        username=owner.username,
        name=owner.name,
        email=owner.email,
        account_id=account.id,
        account_name=account.account_name,
        platform=account.platform,
        publication_type=normalize_publication_type(account.publication_type),
        account_is_active=account.is_active,
        published_url=article.published_url or "",
        latest_traffic_stat=(
            ArticleTrafficStatOut.model_validate(latest_stat)
            if latest_stat is not None
            else None
        ),
    )

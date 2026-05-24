# -*- coding: utf-8 -*-
"""Traffic statistic service functions for article distribution."""

from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.auth.schemas import UserRole

from ..dao import ArticleDistributionDAO
from ..models import ArticleDistributionTrafficStat
from ..schemas import (
    ArticleTrafficStatCreate,
    ArticleTrafficStatOut,
    ArticleTrafficSummaryOut,
    ArticleTrafficSummaryPageOut,
)
from .helpers import (
    article_to_out,
    get_accessible_account,
    get_accessible_article,
    normalize_optional,
    resolve_optional_target_user_id,
)


def list_article_traffic_summaries(
    db: Session,
    *,
    current_user: User,
    user_id: int | None = None,
    account_id: int | None = None,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    publish_status: str | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> ArticleTrafficSummaryPageOut:
    target_user_id = resolve_optional_target_user_id(current_user, user_id)
    if account_id is not None:
        account = get_accessible_account(db, account_id, current_user, write=False)
        if target_user_id is not None and account.user_id != target_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    dao = ArticleDistributionDAO(db)
    articles, total = dao.list_articles_page(
        user_id=target_user_id,
        account_id=account_id,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publish_status=publish_status,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        page=page,
        page_size=page_size,
    )
    article_ids = [article.id for article in articles]
    latest_stats = dao.latest_traffic_stats_by_article_ids(article_ids)
    record_counts = dao.count_traffic_stats_by_article_ids(article_ids)
    return ArticleTrafficSummaryPageOut(
        items=[
            ArticleTrafficSummaryOut(
                article=article_to_out(db, article),
                latest_stat=(
                    ArticleTrafficStatOut.model_validate(latest_stats[article.id])
                    if article.id in latest_stats
                    else None
                ),
                record_count=record_counts.get(article.id, 0),
            )
            for article in articles
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


def list_article_traffic_stats(
    db: Session, *, article_id: int, current_user: User
) -> list[ArticleTrafficStatOut]:
    article = get_accessible_article(db, article_id, current_user)
    return [
        ArticleTrafficStatOut.model_validate(stat)
        for stat in ArticleDistributionDAO(db).list_traffic_stats(article_id=article.id)
    ]


def create_article_traffic_stat(
    db: Session,
    *,
    article_id: int,
    payload: ArticleTrafficStatCreate,
    current_user: User,
) -> ArticleTrafficStatOut:
    article = get_accessible_article(db, article_id, current_user)
    stat = ArticleDistributionTrafficStat(
        user_id=article.user_id,
        account_id=article.account_id,
        article_id=article.id,
        read_count=payload.read_count,
        like_count=payload.like_count,
        favorite_count=payload.favorite_count,
        share_count=payload.share_count,
        recorded_at=_normalize_recorded_at(payload.recorded_at),
    )
    created = ArticleDistributionDAO(db).create_traffic_stat(stat)
    return ArticleTrafficStatOut.model_validate(created)


def delete_article_traffic_stat(
    db: Session, *, stat_id: int, current_user: User
) -> None:
    dao = ArticleDistributionDAO(db)
    stat = dao.get_traffic_stat(stat_id)
    if stat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="统计记录不存在")

    article = dao.get_article(stat.article_id)
    if article is not None:
        get_accessible_article(db, article.id, current_user)
    elif current_user.role != UserRole.ADMIN and stat.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    dao.delete_traffic_stat(stat)


def _normalize_recorded_at(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value

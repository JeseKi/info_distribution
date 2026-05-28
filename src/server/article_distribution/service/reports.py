# -*- coding: utf-8 -*-
"""Report service functions for article distribution."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..dao import ArticleDistributionDAO
from ..schemas import (
    AccountStatusFilter,
    ArticleDistributionMissingTrafficArticleOut,
    ArticleDistributionMissingTrafficPageOut,
    ArticleDistributionMissingTrafficReportOut,
    ArticleDistributionMissingTrafficSummaryOut,
    ArticleDistributionMissingTrafficUserOut,
    ArticleDistributionPendingArticleOut,
    ArticleDistributionPendingUserOut,
    ArticleDistributionPlatformSummaryOut,
    ArticleDistributionPublicArticleOut,
    ArticleDistributionPublicDashboardOut,
    ArticleDistributionReportOut,
    ArticleDistributionReportSummaryOut,
    ArticleTrafficStatOut,
)
from .helpers import (
    normalize_optional,
    normalize_publication_type,
    normalize_publish_status,
)


def list_unpublished_report(
    db: Session,
    *,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "active",
) -> ArticleDistributionReportOut:
    rows = ArticleDistributionDAO(db).list_report_user_summary_rows(
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        account_status=account_status,
    )
    users = [
        ArticleDistributionPendingUserOut(
            user_id=owner.id,
            username=owner.username,
            name=owner.name,
            email=owner.email,
            remaining_count=unpublished_count,
            published_count=published_count,
            invalid_count=invalid_count,
            inactive_account_articles=inactive_account_articles,
            read_count=read_count,
            like_count=like_count,
            favorite_count=favorite_count,
            share_count=share_count,
            platform_summaries=[],
            articles=[],
        )
        for (
            owner,
            published_count,
            unpublished_count,
            invalid_count,
            inactive_account_articles,
            read_count,
            like_count,
            favorite_count,
            share_count,
        ) in rows
    ]
    return ArticleDistributionReportOut(
        summary=ArticleDistributionReportSummaryOut(
            total_users=len(users),
            unpublished_users=sum(1 for user in users if user.remaining_count > 0),
            published_articles=sum(user.published_count for user in users),
            unpublished_articles=sum(user.remaining_count for user in users),
            invalid_articles=sum(user.invalid_count for user in users),
            inactive_account_articles=sum(
                user.inactive_account_articles for user in users
            ),
            read_count=sum(user.read_count for user in users),
            like_count=sum(user.like_count for user in users),
            favorite_count=sum(user.favorite_count for user in users),
            share_count=sum(user.share_count for user in users),
        ),
        users=users,
    )


def get_unpublished_report_user_detail(
    db: Session,
    *,
    user_id: int,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "active",
) -> ArticleDistributionPendingUserOut:
    rows = ArticleDistributionDAO(db).list_report_article_owner_rows(
        user_id=user_id,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        account_status=account_status,
    )
    users = _build_user_reports_from_rows(db, rows)
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户无匹配文章")
    return users[0]


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


def _build_user_reports_from_rows(
    db: Session,
    rows: list[tuple],
) -> list[ArticleDistributionPendingUserOut]:
    grouped: dict[int, ArticleDistributionPendingUserOut] = {}
    platform_summaries: dict[tuple[int, int], ArticleDistributionPlatformSummaryOut] = {}
    latest_traffic_stats = ArticleDistributionDAO(db).latest_traffic_stats_by_article_ids(
        [article.id for article, _, _ in rows]
    )

    for article, account, owner in rows:
        account_is_active = account.is_active
        if owner.id not in grouped:
            grouped[owner.id] = ArticleDistributionPendingUserOut(
                user_id=owner.id,
                username=owner.username,
                name=owner.name,
                email=owner.email,
                remaining_count=0,
                published_count=0,
                invalid_count=0,
                inactive_account_articles=0,
                read_count=0,
                like_count=0,
                favorite_count=0,
                share_count=0,
                platform_summaries=[],
                articles=[],
            )
        user_report = grouped[owner.id]
        if not account_is_active:
            user_report.inactive_account_articles += 1
        latest_stat = latest_traffic_stats.get(article.id)
        if latest_stat is not None:
            user_report.read_count += latest_stat.read_count
            user_report.like_count += latest_stat.like_count
            user_report.favorite_count += latest_stat.favorite_count
            user_report.share_count += latest_stat.share_count
        summary_key = (owner.id, account.id)
        if summary_key not in platform_summaries:
            platform_summary = ArticleDistributionPlatformSummaryOut(
                account_id=account.id,
                account_name=account.account_name,
                platform=account.platform,
                publication_type=normalize_publication_type(account.publication_type),
                account_is_active=account_is_active,
                published_count=0,
                unpublished_count=0,
                invalid_count=0,
                latest_published_url=None,
            )
            platform_summaries[summary_key] = platform_summary
            user_report.platform_summaries.append(platform_summary)
        platform_summary = platform_summaries[summary_key]
        if article.publish_status == "published":
            user_report.published_count += 1
            platform_summary.published_count += 1
            if article.published_url:
                platform_summary.latest_published_url = article.published_url
        elif article.publish_status == "invalid":
            user_report.invalid_count += 1
            platform_summary.invalid_count += 1
        else:
            if account_is_active:
                user_report.remaining_count += 1
                platform_summary.unpublished_count += 1
        user_report.articles.append(
            ArticleDistributionPendingArticleOut(
                id=article.id,
                title=article.title,
                markdown_content=article.markdown_content,
                scheduled_date=article.scheduled_date,
                account_id=account.id,
                account_name=account.account_name,
                platform=account.platform,
                publication_type=normalize_publication_type(account.publication_type),
                account_is_active=account_is_active,
                publish_status=normalize_publish_status(article.publish_status),
                published_url=article.published_url,
                created_at=article.created_at,
                latest_traffic_stat=(
                    ArticleTrafficStatOut.model_validate(latest_traffic_stats[article.id])
                    if article.id in latest_traffic_stats
                    else None
                ),
            )
        )
    return list(grouped.values())


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _recent_scheduled_from(
    requested_scheduled_from: date | None,
    recorded_to: datetime,
) -> date:
    recent_cutoff = (recorded_to - timedelta(hours=168)).date()
    if requested_scheduled_from is None:
        return recent_cutoff
    return max(requested_scheduled_from, recent_cutoff)


def list_public_dashboard(
    db: Session,
    *,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    publication_type: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> ArticleDistributionPublicDashboardOut:
    dao = ArticleDistributionDAO(db)
    summary_rows = dao.list_report_user_summary_rows(
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publication_type=publication_type,
        account_status="active",
    )
    article_rows, total = dao.list_public_published_article_rows_page(
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publication_type=publication_type,
        page=page,
        page_size=page_size,
    )
    latest_traffic_stats = dao.latest_traffic_stats_by_article_ids(
        [article.id for article, _ in article_rows]
    )

    published_articles = [
        ArticleDistributionPublicArticleOut(
            id=article.id,
            title=article.title,
            published_at=article.scheduled_date,
            published_url=article.published_url or "",
            account_name=account.account_name,
            platform=account.platform,
            publication_type=normalize_publication_type(account.publication_type),
            latest_traffic_stat=(
                ArticleTrafficStatOut.model_validate(latest_traffic_stats[article.id])
                if article.id in latest_traffic_stats
                else None
            ),
        )
        for article, account in article_rows
    ]
    return ArticleDistributionPublicDashboardOut(
        summary=ArticleDistributionReportSummaryOut(
            total_users=len(summary_rows),
            unpublished_users=sum(1 for row in summary_rows if row[2] > 0),
            published_articles=sum(row[1] for row in summary_rows),
            unpublished_articles=sum(row[2] for row in summary_rows),
            invalid_articles=sum(row[3] for row in summary_rows),
            inactive_account_articles=sum(row[4] for row in summary_rows),
            read_count=sum(row[5] for row in summary_rows),
            like_count=sum(row[6] for row in summary_rows),
            favorite_count=sum(row[7] for row in summary_rows),
            share_count=sum(row[8] for row in summary_rows),
        ),
        articles=published_articles,
        total=total,
        page=page,
        page_size=page_size,
    )

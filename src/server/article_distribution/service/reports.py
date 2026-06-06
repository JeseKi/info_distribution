# -*- coding: utf-8 -*-
"""Report service functions for article distribution."""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, timezone
from io import StringIO
from typing import TypeAlias, cast

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth.models import User

from ..dao import ArticleDistributionDAO
from ..schemas import (
    AccountStatusFilter,
    ArticleDistributionMissingTrafficArticleOut,
    ArticleDistributionMissingTrafficPageOut,
    ArticleDistributionMissingTrafficReportOut,
    ArticleDistributionMissingTrafficSummaryOut,
    ArticleDistributionMissingTrafficUserOut,
    ArticleDistributionMetadataDashboardArticleOut,
    ArticleDistributionMetadataDashboardOut,
    ArticleDistributionMetadataDashboardSummaryOut,
    ArticleDistributionMetadataDashboardTopicOut,
    ArticleDistributionOverviewArticleOut,
    ArticleDistributionOverviewOut,
    ArticleDistributionOverviewSummaryOut,
    ArticleDistributionOverviewTopicOut,
    ArticleDistributionOverviewUserOut,
    ArticleDistributionOverviewView,
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
    assert_admin,
    normalize_optional,
    normalize_publication_type,
    normalize_publish_status,
)

OverviewItemOut: TypeAlias = (
    ArticleDistributionOverviewUserOut
    | ArticleDistributionOverviewArticleOut
    | ArticleDistributionOverviewTopicOut
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


def list_metadata_dashboard(
    db: Session,
    *,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "active",
    publish_status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ArticleDistributionMetadataDashboardOut:
    dao = ArticleDistributionDAO(db)
    rows, total = dao.list_metadata_dashboard_article_rows_page(
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        account_status=account_status,
        publish_status=publish_status,
        page=page,
        page_size=page_size,
    )
    latest_traffic_stats = dao.latest_traffic_stats_by_article_ids(
        [article.id for article, _ in rows]
    )

    grouped: dict[str, ArticleDistributionMetadataDashboardTopicOut] = {}
    material_set: set[str] = set()
    for article, account in rows:
        metadata = (
            article.article_metadata
            if isinstance(article.article_metadata, dict)
            else None
        )
        group_key = _metadata_output_id(metadata) or f"article:{article.id}"
        topic = (
            _metadata_topic(metadata)
            or _metadata_output_id(metadata)
            or "未设置选题"
        )
        latest_stat = latest_traffic_stats.get(article.id)
        materials = _metadata_material_titles(metadata)
        material_set.update(materials)

        if group_key not in grouped:
            grouped[group_key] = ArticleDistributionMetadataDashboardTopicOut(
                key=group_key,
                output_id=_metadata_output_id(metadata),
                topic=topic,
                materials=[],
                article_count=0,
                read_count=0,
                like_count=0,
                favorite_count=0,
                share_count=0,
                articles=[],
            )

        topic_row = grouped[group_key]
        metadata_topic = _metadata_topic(metadata)
        if metadata_topic is not None:
            topic_row.topic = metadata_topic
        elif topic_row.topic == "未设置选题" and topic != "未设置选题":
            topic_row.topic = topic
        topic_row.materials = _merge_unique(topic_row.materials, materials)
        topic_row.article_count += 1
        if latest_stat is not None:
            topic_row.read_count += latest_stat.read_count
            topic_row.like_count += latest_stat.like_count
            topic_row.favorite_count += latest_stat.favorite_count
            topic_row.share_count += latest_stat.share_count
        topic_row.articles.append(
            ArticleDistributionMetadataDashboardArticleOut(
                id=article.id,
                title=article.title,
                markdown_content=article.markdown_content,
                scheduled_date=article.scheduled_date,
                publish_status=normalize_publish_status(article.publish_status),
                published_url=article.published_url,
                account_id=account.id,
                account_name=account.account_name,
                platform=account.platform,
                publication_type=normalize_publication_type(account.publication_type),
                account_is_active=account.is_active,
                article_role=_metadata_article_string(metadata, "role"),
                angle_label=_metadata_string(metadata, "angle_label"),
                audience_label=_metadata_string(metadata, "audience_label"),
                summary=_metadata_article_string(metadata, "summary"),
                metadata=metadata,
                latest_traffic_stat=(
                    ArticleTrafficStatOut.model_validate(latest_stat)
                    if latest_stat is not None
                    else None
                ),
            )
        )

    topics = list(grouped.values())
    return ArticleDistributionMetadataDashboardOut(
        summary=ArticleDistributionMetadataDashboardSummaryOut(
            topic_count=len(topics),
            article_count=sum(topic.article_count for topic in topics),
            material_count=len(material_set),
            read_count=sum(topic.read_count for topic in topics),
            like_count=sum(topic.like_count for topic in topics),
            favorite_count=sum(topic.favorite_count for topic in topics),
            share_count=sum(topic.share_count for topic in topics),
        ),
        topics=topics,
        total=total,
        page=page,
        page_size=page_size,
    )


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
        topics = _overview_topics_from_articles(all_articles)
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

    users = _overview_users_from_articles(all_articles)
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


def _metadata_output_id(metadata: dict | None) -> str | None:
    return _metadata_string(metadata, "output_id")


def _metadata_topic(metadata: dict | None) -> str | None:
    return _metadata_string(metadata, "topic")


def _metadata_string(metadata: dict | None, key: str) -> str | None:
    if not metadata:
        return None
    value = metadata.get(key)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _metadata_article_string(metadata: dict | None, key: str) -> str | None:
    if not metadata:
        return None
    article = metadata.get("article")
    if not isinstance(article, dict):
        return None
    value = article.get(key)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _metadata_material_titles(metadata: dict | None) -> list[str]:
    if not metadata:
        return []
    article = metadata.get("article")
    if not isinstance(article, dict):
        return []
    materials = article.get("materials_used")
    if not isinstance(materials, list):
        return []

    titles: list[str] = []
    for material in materials:
        if not isinstance(material, dict):
            continue
        title = material.get("title")
        if not isinstance(title, str):
            continue
        normalized = title.strip()
        if normalized:
            titles.append(normalized)
    return _merge_unique([], titles)


def _merge_unique(current: list[str], additions: list[str]) -> list[str]:
    seen = set(current)
    merged = list(current)
    for item in additions:
        if item in seen:
            continue
        seen.add(item)
        merged.append(item)
    return merged


def _overview_articles_from_rows(
    db: Session,
    rows: list[tuple],
    *,
    recorded_from: datetime | None,
    recorded_to: datetime | None,
) -> list[ArticleDistributionOverviewArticleOut]:
    dao = ArticleDistributionDAO(db)
    article_ids = [article.id for article, _, _ in rows]
    latest_traffic_stats = dao.latest_traffic_stats_by_article_ids(article_ids)
    traffic_article_ids: set[int] = set()
    if recorded_from is not None and recorded_to is not None:
        traffic_article_ids = dao.traffic_article_ids_in_range(
            article_ids,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
        )

    articles: list[ArticleDistributionOverviewArticleOut] = []
    for article, account, owner in rows:
        metadata = (
            article.article_metadata
            if isinstance(article.article_metadata, dict)
            else None
        )
        latest_stat = latest_traffic_stats.get(article.id)
        articles.append(
            ArticleDistributionOverviewArticleOut(
                id=article.id,
                title=article.title,
                markdown_content=article.markdown_content,
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
                publish_status=normalize_publish_status(article.publish_status),
                published_url=article.published_url,
                created_at=article.created_at,
                missing_traffic=(
                    recorded_from is not None
                    and recorded_to is not None
                    and article.publish_status == "published"
                    and bool(article.published_url)
                    and article.id not in traffic_article_ids
                ),
                output_id=_metadata_output_id(metadata),
                topic=_metadata_topic(metadata),
                materials=_metadata_material_titles(metadata),
                article_role=_metadata_article_string(metadata, "role"),
                angle_label=_metadata_string(metadata, "angle_label"),
                audience_label=_metadata_string(metadata, "audience_label"),
                summary=_metadata_article_string(metadata, "summary"),
                metadata=metadata,
                latest_traffic_stat=(
                    ArticleTrafficStatOut.model_validate(latest_stat)
                    if latest_stat is not None
                    else None
                ),
            )
        )
    return articles


def _overview_users_from_articles(
    articles: list[ArticleDistributionOverviewArticleOut],
) -> list[ArticleDistributionOverviewUserOut]:
    grouped: dict[int, ArticleDistributionOverviewUserOut] = {}
    platform_summaries: dict[tuple[int, int], ArticleDistributionPlatformSummaryOut] = {}

    for article in articles:
        if article.user_id not in grouped:
            grouped[article.user_id] = ArticleDistributionOverviewUserOut(
                user_id=article.user_id,
                username=article.username,
                name=article.name,
                email=article.email,
                platform_summaries=[],
                articles=[],
            )
        user_report = grouped[article.user_id]
        if not article.account_is_active:
            user_report.inactive_account_articles += 1
        if article.missing_traffic:
            user_report.missing_count += 1
        latest_stat = article.latest_traffic_stat
        if latest_stat is not None:
            user_report.read_count += latest_stat.read_count
            user_report.like_count += latest_stat.like_count
            user_report.favorite_count += latest_stat.favorite_count
            user_report.share_count += latest_stat.share_count

        summary_key = (article.user_id, article.account_id)
        if summary_key not in platform_summaries:
            platform_summary = ArticleDistributionPlatformSummaryOut(
                account_id=article.account_id,
                account_name=article.account_name,
                platform=article.platform,
                publication_type=article.publication_type,
                account_is_active=article.account_is_active,
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
        elif article.account_is_active:
            user_report.remaining_count += 1
            platform_summary.unpublished_count += 1
        user_report.articles.append(article)

    return list(grouped.values())


def _overview_topics_from_articles(
    articles: list[ArticleDistributionOverviewArticleOut],
) -> list[ArticleDistributionOverviewTopicOut]:
    grouped: dict[str, ArticleDistributionOverviewTopicOut] = {}
    for article in articles:
        group_key = article.output_id or f"article:{article.id}"
        topic = article.topic or article.output_id or "未设置选题"
        if group_key not in grouped:
            grouped[group_key] = ArticleDistributionOverviewTopicOut(
                key=group_key,
                output_id=article.output_id,
                topic=topic,
                materials=[],
                article_count=0,
                articles=[],
            )
        topic_row = grouped[group_key]
        if article.topic is not None:
            topic_row.topic = article.topic
        elif topic_row.topic == "未设置选题" and topic != "未设置选题":
            topic_row.topic = topic
        topic_row.materials = _merge_unique(topic_row.materials, article.materials)
        topic_row.article_count += 1
        latest_stat = article.latest_traffic_stat
        if latest_stat is not None:
            topic_row.read_count += latest_stat.read_count
            topic_row.like_count += latest_stat.like_count
            topic_row.favorite_count += latest_stat.favorite_count
            topic_row.share_count += latest_stat.share_count
        topic_row.articles.append(article)
    return list(grouped.values())


def _overview_summary(
    articles: list[ArticleDistributionOverviewArticleOut],
) -> ArticleDistributionOverviewSummaryOut:
    users = {article.user_id for article in articles}
    topics = _overview_topics_from_articles(articles)
    materials = {
        material
        for topic in topics
        for material in topic.materials
    }
    return ArticleDistributionOverviewSummaryOut(
        total_users=len(users),
        total_articles=len(articles),
        published_articles=sum(1 for article in articles if article.publish_status == "published"),
        unpublished_articles=sum(
            1
            for article in articles
            if article.publish_status == "unpublished" and article.account_is_active
        ),
        invalid_articles=sum(1 for article in articles if article.publish_status == "invalid"),
        inactive_account_articles=sum(1 for article in articles if not article.account_is_active),
        missing_articles=sum(1 for article in articles if article.missing_traffic),
        topic_count=len(topics),
        material_count=len(materials),
        read_count=sum(
            article.latest_traffic_stat.read_count
            for article in articles
            if article.latest_traffic_stat is not None
        ),
        like_count=sum(
            article.latest_traffic_stat.like_count
            for article in articles
            if article.latest_traffic_stat is not None
        ),
        favorite_count=sum(
            article.latest_traffic_stat.favorite_count
            for article in articles
            if article.latest_traffic_stat is not None
        ),
        share_count=sum(
            article.latest_traffic_stat.share_count
            for article in articles
            if article.latest_traffic_stat is not None
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


PUBLICITY_RECORD_CSV_HEADERS = [
    "文章ID",
    "发布日期",
    "负责人ID",
    "负责人",
    "用户名",
    "邮箱",
    "平台",
    "发布账号",
    "发布类型",
    "账号状态",
    "标题",
    "链接",
    "最近阅读量",
    "最近点赞量",
    "最近收藏量",
    "最近转发量",
    "最近统计时间",
]

PUBLICATION_TYPE_LABELS = {
    "video": "视频",
    "article": "文章",
    "image_text": "图文",
}


def build_publicity_records_csv(
    db: Session,
    *,
    current_user: User,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "all",
) -> str:
    assert_admin(current_user)
    effective_scheduled_to = scheduled_to or date.today()
    if scheduled_from is not None and scheduled_from > effective_scheduled_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="计划日期范围无效",
        )

    dao = ArticleDistributionDAO(db)
    rows = dao.list_publicity_record_rows(
        scheduled_from=scheduled_from,
        scheduled_to=effective_scheduled_to,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        account_status=account_status,
    )
    latest_traffic_stats = dao.latest_traffic_stats_by_article_ids(
        [article.id for article, _, _ in rows]
    )

    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(PUBLICITY_RECORD_CSV_HEADERS)
    for article, account, owner in rows:
        latest_stat = latest_traffic_stats.get(article.id)
        writer.writerow(
            [
                article.id,
                article.scheduled_date.isoformat(),
                owner.id,
                owner.name or owner.username,
                owner.username,
                owner.email,
                account.platform,
                account.account_name,
                PUBLICATION_TYPE_LABELS.get(
                    account.publication_type, account.publication_type
                ),
                "启用" if account.is_active else "停用",
                article.title,
                article.published_url or "",
                latest_stat.read_count if latest_stat is not None else "",
                latest_stat.like_count if latest_stat is not None else "",
                latest_stat.favorite_count if latest_stat is not None else "",
                latest_stat.share_count if latest_stat is not None else "",
                latest_stat.recorded_at.isoformat() if latest_stat is not None else "",
            ]
        )
    return "\ufeff" + output.getvalue()

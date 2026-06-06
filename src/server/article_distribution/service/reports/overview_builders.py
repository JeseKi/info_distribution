# -*- coding: utf-8 -*-
"""Builders for report overview responses."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ...dao import ArticleDistributionDAO
from ...schemas import (
    ArticleDistributionOverviewArticleDetailOut,
    ArticleDistributionOverviewArticleOut,
    ArticleDistributionOverviewSummaryOut,
    ArticleDistributionOverviewTopicOut,
    ArticleDistributionOverviewUserOut,
    ArticleDistributionPlatformSummaryOut,
    ArticleTrafficStatOut,
)
from ..helpers import normalize_publication_type, normalize_publish_status
from .metadata_utils import (
    _merge_unique,
    _metadata_article_string,
    _metadata_material_titles,
    _metadata_output_id,
    _metadata_string,
    _metadata_topic,
)

def _overview_articles_from_rows(
    db: Session,
    rows: list[tuple],
    *,
    recorded_from: datetime | None,
    recorded_to: datetime | None,
    include_detail_fields: bool = False,
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
        article_out_fields = {
                "id": article.id,
                "title": article.title,
                "scheduled_date": article.scheduled_date,
                "user_id": owner.id,
                "username": owner.username,
                "name": owner.name,
                "email": owner.email,
                "account_id": account.id,
                "account_name": account.account_name,
                "platform": account.platform,
                "publication_type": normalize_publication_type(account.publication_type),
                "account_is_active": account.is_active,
                "publish_status": normalize_publish_status(article.publish_status),
                "published_url": article.published_url,
                "created_at": article.created_at,
                "missing_traffic": (
                    recorded_from is not None
                    and recorded_to is not None
                    and article.publish_status == "published"
                    and bool(article.published_url)
                    and article.id not in traffic_article_ids
                ),
                "output_id": _metadata_output_id(metadata),
                "topic": _metadata_topic(metadata),
                "materials": _metadata_material_titles(metadata),
                "article_role": _metadata_article_string(metadata, "role"),
                "angle_label": _metadata_string(metadata, "angle_label"),
                "audience_label": _metadata_string(metadata, "audience_label"),
                "latest_traffic_stat": (
                    ArticleTrafficStatOut.model_validate(latest_stat)
                    if latest_stat is not None
                    else None
                ),
            }
        if include_detail_fields:
            articles.append(
                ArticleDistributionOverviewArticleDetailOut(
                    **article_out_fields,
                    markdown_content=article.markdown_content,
                    summary=_metadata_article_string(metadata, "summary"),
                    metadata=metadata,
                )
            )
        else:
            articles.append(
                ArticleDistributionOverviewArticleOut(
                    **article_out_fields,
                )
            )
    return articles


def _overview_users_from_articles(
    articles: list[ArticleDistributionOverviewArticleOut],
    *,
    include_articles: bool = True,
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
        if include_articles:
            user_report.articles.append(article)

    return list(grouped.values())


def _overview_topics_from_articles(
    articles: list[ArticleDistributionOverviewArticleOut],
    *,
    include_articles: bool = True,
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
        if include_articles:
            topic_row.articles.append(article)
    return list(grouped.values())


def _overview_summary(
    articles: list[ArticleDistributionOverviewArticleOut],
) -> ArticleDistributionOverviewSummaryOut:
    users = {article.user_id for article in articles}
    topics = _overview_topics_from_articles(articles, include_articles=False)
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

# -*- coding: utf-8 -*-
"""Metadata dashboard report service."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from ...dao import ArticleDistributionDAO
from ...schemas import (
    AccountStatusFilter,
    ArticleDistributionMetadataDashboardArticleOut,
    ArticleDistributionMetadataDashboardOut,
    ArticleDistributionMetadataDashboardSummaryOut,
    ArticleDistributionMetadataDashboardTopicOut,
    ArticleTrafficStatOut,
)
from ..helpers import (
    normalize_optional,
    normalize_publication_type,
    normalize_publish_status,
)
from .metadata_utils import (
    _merge_unique,
    _metadata_article_string,
    _metadata_material_titles,
    _metadata_output_id,
    _metadata_string,
    _metadata_topic,
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

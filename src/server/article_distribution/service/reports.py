# -*- coding: utf-8 -*-
"""Report service functions for article distribution."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from ..dao import ArticleDistributionDAO
from ..schemas import (
    AccountStatusFilter,
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
    grouped: dict[int, ArticleDistributionPendingUserOut] = {}
    platform_summaries: dict[tuple[int, int], ArticleDistributionPlatformSummaryOut] = {}
    rows = ArticleDistributionDAO(db).list_report_article_owner_rows(
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        account_status=account_status,
    )
    latest_traffic_stats = ArticleDistributionDAO(db).latest_traffic_stats_by_article_ids(
        [article.id for article, _, _ in rows]
    )
    inactive_account_articles = 0
    for article, account, owner in rows:
        account_is_active = account.is_active
        if not account_is_active:
            inactive_account_articles += 1
        if owner.id not in grouped:
            grouped[owner.id] = ArticleDistributionPendingUserOut(
                user_id=owner.id,
                username=owner.username,
                name=owner.name,
                email=owner.email,
                remaining_count=0,
                published_count=0,
                invalid_count=0,
                platform_summaries=[],
                articles=[],
            )
        user_report = grouped[owner.id]
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
    users = list(grouped.values())
    return ArticleDistributionReportOut(
        summary=ArticleDistributionReportSummaryOut(
            total_users=len(users),
            unpublished_users=sum(1 for user in users if user.remaining_count > 0),
            published_articles=sum(user.published_count for user in users),
            unpublished_articles=sum(user.remaining_count for user in users),
            invalid_articles=sum(user.invalid_count for user in users),
            inactive_account_articles=inactive_account_articles,
        ),
        users=users,
    )


def list_public_dashboard(
    db: Session,
    *,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    publication_type: str | None = None,
) -> ArticleDistributionPublicDashboardOut:
    rows = ArticleDistributionDAO(db).list_report_article_owner_rows(
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publication_type=publication_type,
        account_status="active",
    )
    latest_traffic_stats = ArticleDistributionDAO(db).latest_traffic_stats_by_article_ids(
        [article.id for article, _, _ in rows]
    )

    user_counts: dict[int, dict[str, int]] = {}
    published_articles: list[ArticleDistributionPublicArticleOut] = []
    for article, account, owner in rows:
        counts = user_counts.setdefault(
            owner.id,
            {"published": 0, "unpublished": 0, "invalid": 0},
        )
        if article.publish_status == "published":
            counts["published"] += 1
            if article.published_url:
                published_articles.append(
                    ArticleDistributionPublicArticleOut(
                        id=article.id,
                        title=article.title,
                        published_at=article.scheduled_date,
                        published_url=article.published_url,
                        account_name=account.account_name,
                        platform=account.platform,
                        publication_type=normalize_publication_type(
                            account.publication_type
                        ),
                        latest_traffic_stat=(
                            ArticleTrafficStatOut.model_validate(
                                latest_traffic_stats[article.id]
                            )
                            if article.id in latest_traffic_stats
                            else None
                        ),
                    )
                )
        elif article.publish_status == "invalid":
            counts["invalid"] += 1
        else:
            counts["unpublished"] += 1

    published_articles.sort(key=lambda item: (item.published_at, item.id), reverse=True)
    return ArticleDistributionPublicDashboardOut(
        summary=ArticleDistributionReportSummaryOut(
            total_users=len(user_counts),
            unpublished_users=sum(
                1 for counts in user_counts.values() if counts["unpublished"] > 0
            ),
            published_articles=sum(counts["published"] for counts in user_counts.values()),
            unpublished_articles=sum(
                counts["unpublished"] for counts in user_counts.values()
            ),
            invalid_articles=sum(counts["invalid"] for counts in user_counts.values()),
            inactive_account_articles=0,
        ),
        articles=published_articles,
    )

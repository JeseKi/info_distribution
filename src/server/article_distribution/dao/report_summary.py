# -*- coding: utf-8 -*-
"""Summary and public report DAO methods for article distribution."""

from __future__ import annotations

from datetime import date

from sqlalchemy import case, func

from src.server.auth.models import User

from ..models import ArticleDistributionAccount, ArticleDistributionArticle
from .report_core import ArticleDistributionReportQueryDAO


class ArticleDistributionReportSummaryDAO(ArticleDistributionReportQueryDAO):
    def list_report_article_owner_rows(
        self,
        *,
        user_id: int | None = None,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        account_status: str = "active",
    ) -> list[
        tuple[ArticleDistributionArticle, ArticleDistributionAccount, User]
    ]:
        query = self._report_query(
            user_id=user_id,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
        ).with_entities(
            ArticleDistributionArticle,
            ArticleDistributionAccount,
            User,
        )
        rows = (
            query.order_by(
                User.id.asc(),
                ArticleDistributionArticle.scheduled_date.asc(),
                ArticleDistributionArticle.id.asc(),
            )
            .all()
        )
        return [(article, account, owner) for article, account, owner in rows]

    def list_report_user_summary_rows(
        self,
        *,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        account_status: str = "active",
    ) -> list[tuple[User, int, int, int, int, int, int, int, int]]:
        latest_stats = self._latest_traffic_stat_subquery()
        query = self._report_query(
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
        ).outerjoin(
            latest_stats,
            latest_stats.c.article_id == ArticleDistributionArticle.id,
        )
        rows = (
            query.with_entities(
                User,
                func.sum(
                    case(
                        (ArticleDistributionArticle.publish_status == "published", 1),
                        else_=0,
                    )
                ).label("published_count"),
                func.sum(
                    case(
                        (
                            (
                                ArticleDistributionArticle.publish_status
                                == "unpublished"
                            )
                            & ArticleDistributionAccount.is_active.is_(True),
                            1,
                        ),
                        else_=0,
                    )
                ).label("unpublished_count"),
                func.sum(
                    case(
                        (ArticleDistributionArticle.publish_status == "invalid", 1),
                        else_=0,
                    )
                ).label("invalid_count"),
                func.sum(
                    case(
                        (ArticleDistributionAccount.is_active.is_(False), 1),
                        else_=0,
                    )
                ).label("inactive_account_articles"),
                func.coalesce(func.sum(latest_stats.c.read_count), 0).label(
                    "read_count"
                ),
                func.coalesce(func.sum(latest_stats.c.like_count), 0).label(
                    "like_count"
                ),
                func.coalesce(func.sum(latest_stats.c.favorite_count), 0).label(
                    "favorite_count"
                ),
                func.coalesce(func.sum(latest_stats.c.share_count), 0).label(
                    "share_count"
                ),
            )
            .group_by(User.id)
            .order_by(User.id.asc())
            .all()
        )
        return [
            (
                owner,
                int(published_count or 0),
                int(unpublished_count or 0),
                int(invalid_count or 0),
                int(inactive_account_articles or 0),
                int(read_count or 0),
                int(like_count or 0),
                int(favorite_count or 0),
                int(share_count or 0),
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

    def list_public_published_article_rows_page(
        self,
        *,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        publication_type: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[tuple[ArticleDistributionArticle, ArticleDistributionAccount]], int]:
        query = (
            self._report_query(
                scheduled_from=scheduled_from,
                scheduled_to=scheduled_to,
                publication_type=publication_type,
                account_status="active",
            )
            .filter(
                ArticleDistributionArticle.publish_status == "published",
                ArticleDistributionArticle.published_url.isnot(None),
            )
            .with_entities(ArticleDistributionArticle, ArticleDistributionAccount)
        )
        total = query.count()
        rows = (
            query.order_by(
                ArticleDistributionArticle.scheduled_date.desc(),
                ArticleDistributionArticle.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [(article, account) for article, account in rows], total

    def list_publicity_record_rows(
        self,
        *,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        account_status: str = "all",
    ) -> list[
        tuple[ArticleDistributionArticle, ArticleDistributionAccount, User]
    ]:
        rows = (
            self._report_query(
                scheduled_from=scheduled_from,
                scheduled_to=scheduled_to,
                platform=platform,
                publication_type=publication_type,
                account_status=account_status,
            )
            .filter(
                ArticleDistributionArticle.publish_status == "published",
                ArticleDistributionArticle.published_url.isnot(None),
                ArticleDistributionArticle.published_url != "",
            )
            .with_entities(
                ArticleDistributionArticle,
                ArticleDistributionAccount,
                User,
            )
            .order_by(
                ArticleDistributionArticle.scheduled_date.desc(),
                User.id.asc(),
                ArticleDistributionAccount.platform.asc(),
                ArticleDistributionAccount.account_name.asc(),
                ArticleDistributionArticle.id.desc(),
            )
            .all()
        )
        return [(article, account, owner) for article, account, owner in rows]

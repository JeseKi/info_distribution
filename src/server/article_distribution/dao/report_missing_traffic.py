# -*- coding: utf-8 -*-
"""Missing traffic report DAO methods for article distribution."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Query

from src.server.auth.models import User

from ..models import (
    ArticleDistributionAccount,
    ArticleDistributionArticle,
    ArticleDistributionTrafficStat,
)
from .report_core import ArticleDistributionReportQueryDAO


class ArticleDistributionReportMissingTrafficDAO(ArticleDistributionReportQueryDAO):
    def list_missing_traffic_article_rows_page(
        self,
        *,
        recorded_from: datetime,
        recorded_to: datetime,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        account_status: str = "active",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[
        list[tuple[ArticleDistributionArticle, ArticleDistributionAccount, User]], int
    ]:
        query = (
            self._missing_traffic_query(
                recorded_from=recorded_from,
                recorded_to=recorded_to,
                scheduled_from=scheduled_from,
                scheduled_to=scheduled_to,
                platform=platform,
                publication_type=publication_type,
                account_status=account_status,
            )
            .with_entities(
                ArticleDistributionArticle,
                ArticleDistributionAccount,
                User,
            )
        )
        total = query.count()
        rows = (
            query.order_by(
                ArticleDistributionArticle.scheduled_date.desc(),
                User.id.asc(),
                ArticleDistributionArticle.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [(article, account, owner) for article, account, owner in rows], total

    def list_missing_traffic_article_owner_rows(
        self,
        *,
        recorded_from: datetime,
        recorded_to: datetime,
        user_id: int | None = None,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        account_status: str = "active",
    ) -> list[
        tuple[ArticleDistributionArticle, ArticleDistributionAccount, User]
    ]:
        query = self._missing_traffic_query(
            recorded_from=recorded_from,
            recorded_to=recorded_to,
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
                ArticleDistributionArticle.scheduled_date.desc(),
                ArticleDistributionArticle.id.desc(),
            )
            .all()
        )
        return [(article, account, owner) for article, account, owner in rows]

    def _missing_traffic_query(
        self,
        *,
        recorded_from: datetime,
        recorded_to: datetime,
        user_id: int | None = None,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        account_status: str = "active",
    ) -> Query[ArticleDistributionArticle]:
        recorded_in_range = (
            self.db_session.query(ArticleDistributionTrafficStat.id)
            .filter(
                ArticleDistributionTrafficStat.article_id
                == ArticleDistributionArticle.id,
                ArticleDistributionTrafficStat.recorded_at >= recorded_from,
                ArticleDistributionTrafficStat.recorded_at < recorded_to,
            )
            .exists()
        )
        return self._report_query(
            user_id=user_id,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
        ).filter(
            ArticleDistributionArticle.publish_status == "published",
            ArticleDistributionArticle.published_url.isnot(None),
            ~recorded_in_range,
        )

# -*- coding: utf-8 -*-
"""Shared report query helpers for article distribution."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Query

from src.server.auth.models import User

from ..models import (
    ArticleDistributionAccount,
    ArticleDistributionArticle,
    ArticleDistributionTrafficStat,
)
from .base import ArticleDistributionBaseDAO


class ArticleDistributionReportQueryDAO(ArticleDistributionBaseDAO):
    def _report_query(
        self,
        *,
        user_id: int | None = None,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        account_status: str = "active",
    ) -> Query[ArticleDistributionArticle]:
        query = (
            self.db_session.query(ArticleDistributionArticle)
            .join(
                ArticleDistributionAccount,
                ArticleDistributionArticle.account_id
                == ArticleDistributionAccount.id,
            )
            .join(User, ArticleDistributionArticle.user_id == User.id)
        )
        if user_id is not None:
            query = query.filter(ArticleDistributionArticle.user_id == user_id)
        if scheduled_from is not None:
            query = query.filter(
                ArticleDistributionArticle.scheduled_date >= scheduled_from
            )
        if scheduled_to is not None:
            query = query.filter(
                ArticleDistributionArticle.scheduled_date <= scheduled_to
            )
        if platform:
            query = query.filter(ArticleDistributionAccount.platform == platform)
        if publication_type:
            query = query.filter(
                ArticleDistributionAccount.publication_type == publication_type
            )
        if account_status == "active":
            query = query.filter(ArticleDistributionAccount.is_active.is_(True))
        elif account_status == "inactive":
            query = query.filter(ArticleDistributionAccount.is_active.is_(False))
        return query

    def _latest_traffic_stat_subquery(self):
        ranked_stats = (
            self.db_session.query(
                ArticleDistributionTrafficStat.article_id.label("article_id"),
                ArticleDistributionTrafficStat.read_count.label("read_count"),
                ArticleDistributionTrafficStat.like_count.label("like_count"),
                ArticleDistributionTrafficStat.favorite_count.label("favorite_count"),
                ArticleDistributionTrafficStat.share_count.label("share_count"),
                func.row_number()
                .over(
                    partition_by=ArticleDistributionTrafficStat.article_id,
                    order_by=[
                        ArticleDistributionTrafficStat.recorded_at.desc(),
                        ArticleDistributionTrafficStat.id.desc(),
                    ],
                )
                .label("rank"),
            )
            .subquery()
        )
        return (
            self.db_session.query(
                ranked_stats.c.article_id,
                ranked_stats.c.read_count,
                ranked_stats.c.like_count,
                ranked_stats.c.favorite_count,
                ranked_stats.c.share_count,
            )
            .filter(ranked_stats.c.rank == 1)
            .subquery()
        )

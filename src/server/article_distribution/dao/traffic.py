# -*- coding: utf-8 -*-
"""Traffic stat DAO methods for article distribution."""

from __future__ import annotations

from sqlalchemy import func

from ..models import ArticleDistributionTrafficStat
from .base import ArticleDistributionBaseDAO


class ArticleDistributionTrafficDAO(ArticleDistributionBaseDAO):
    def create_traffic_stat(
        self, stat: ArticleDistributionTrafficStat
    ) -> ArticleDistributionTrafficStat:
        self.db_session.add(stat)
        self.db_session.commit()
        self.db_session.refresh(stat)
        return stat

    def get_traffic_stat(
        self, stat_id: int
    ) -> ArticleDistributionTrafficStat | None:
        return (
            self.db_session.query(ArticleDistributionTrafficStat)
            .filter(ArticleDistributionTrafficStat.id == stat_id)
            .first()
        )

    def list_traffic_stats(
        self, *, article_id: int
    ) -> list[ArticleDistributionTrafficStat]:
        return (
            self.db_session.query(ArticleDistributionTrafficStat)
            .filter(ArticleDistributionTrafficStat.article_id == article_id)
            .order_by(
                ArticleDistributionTrafficStat.recorded_at.desc(),
                ArticleDistributionTrafficStat.id.desc(),
            )
            .all()
        )

    def latest_traffic_stats_by_article_ids(
        self, article_ids: list[int]
    ) -> dict[int, ArticleDistributionTrafficStat]:
        if not article_ids:
            return {}
        stats = (
            self.db_session.query(ArticleDistributionTrafficStat)
            .filter(ArticleDistributionTrafficStat.article_id.in_(article_ids))
            .order_by(
                ArticleDistributionTrafficStat.article_id.asc(),
                ArticleDistributionTrafficStat.recorded_at.desc(),
                ArticleDistributionTrafficStat.id.desc(),
            )
            .all()
        )
        latest: dict[int, ArticleDistributionTrafficStat] = {}
        for stat in stats:
            latest.setdefault(stat.article_id, stat)
        return latest

    def count_traffic_stats_by_article_ids(
        self, article_ids: list[int]
    ) -> dict[int, int]:
        if not article_ids:
            return {}
        rows = (
            self.db_session.query(
                ArticleDistributionTrafficStat.article_id,
                func.count(ArticleDistributionTrafficStat.id),
            )
            .filter(ArticleDistributionTrafficStat.article_id.in_(article_ids))
            .group_by(ArticleDistributionTrafficStat.article_id)
            .all()
        )
        return {int(article_id): int(count) for article_id, count in rows}

    def delete_traffic_stat(self, stat: ArticleDistributionTrafficStat) -> None:
        self.db_session.delete(stat)
        self.db_session.commit()

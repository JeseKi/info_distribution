# -*- coding: utf-8 -*-
"""Overview and metadata dashboard DAO methods for article distribution."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import String, cast, literal, or_
from sqlalchemy.orm import Query

from src.server.auth.models import User

from ..models import (
    ArticleDistributionAccount,
    ArticleDistributionArticle,
    ArticleDistributionTrafficStat,
)
from .report_core import ArticleDistributionReportQueryDAO


class ArticleDistributionReportOverviewDAO(ArticleDistributionReportQueryDAO):
    def list_metadata_dashboard_article_rows_page(
        self,
        *,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        account_status: str = "active",
        publish_status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[tuple[ArticleDistributionArticle, ArticleDistributionAccount]], int]:
        query = self._report_query(
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
        )
        if publish_status:
            query = query.filter(
                ArticleDistributionArticle.publish_status == publish_status
            )
        identity_filter = self._metadata_dashboard_identity_filter()
        identity_total = query.filter(identity_filter).count()
        if identity_total > 0:
            query = query.filter(identity_filter)
            total = identity_total
        else:
            total = query.count()
        rows = (
            query.with_entities(
                ArticleDistributionArticle,
                ArticleDistributionAccount,
            )
            .order_by(ArticleDistributionArticle.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [(article, account) for article, account in rows], total

    def list_overview_article_owner_rows(
        self,
        *,
        user_id: int | None = None,
        topic_key: str | None = None,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        project_id: int | None = None,
        theme_id: int | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        account_status: str = "active",
        publish_status: str | None = None,
        keyword: str | None = None,
        missing_traffic_only: bool = False,
        recorded_from: datetime | None = None,
        recorded_to: datetime | None = None,
    ) -> list[
        tuple[ArticleDistributionArticle, ArticleDistributionAccount, User]
    ]:
        query = self._overview_query(
            user_id=user_id,
            topic_key=topic_key,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            project_id=project_id,
            theme_id=theme_id,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
            publish_status=publish_status,
            keyword=keyword,
            missing_traffic_only=missing_traffic_only,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
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

    def list_overview_article_owner_rows_page(
        self,
        *,
        user_id: int | None = None,
        topic_key: str | None = None,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        project_id: int | None = None,
        theme_id: int | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        account_status: str = "active",
        publish_status: str | None = None,
        keyword: str | None = None,
        missing_traffic_only: bool = False,
        recorded_from: datetime | None = None,
        recorded_to: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[
        list[tuple[ArticleDistributionArticle, ArticleDistributionAccount, User]], int
    ]:
        query = self._overview_query(
            user_id=user_id,
            topic_key=topic_key,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            project_id=project_id,
            theme_id=theme_id,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
            publish_status=publish_status,
            keyword=keyword,
            missing_traffic_only=missing_traffic_only,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
        ).with_entities(
            ArticleDistributionArticle,
            ArticleDistributionAccount,
            User,
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

    def get_overview_article_owner_row(
        self,
        article_id: int,
    ) -> tuple[ArticleDistributionArticle, ArticleDistributionAccount, User] | None:
        row = (
            self._overview_query(account_status="all")
            .with_entities(
                ArticleDistributionArticle,
                ArticleDistributionAccount,
                User,
            )
            .filter(ArticleDistributionArticle.id == article_id)
            .first()
        )
        if row is None:
            return None
        article, account, owner = row
        return article, account, owner

    def traffic_article_ids_in_range(
        self,
        article_ids: list[int],
        *,
        recorded_from: datetime,
        recorded_to: datetime,
    ) -> set[int]:
        if not article_ids:
            return set()
        rows = (
            self.db_session.query(ArticleDistributionTrafficStat.article_id)
            .filter(
                ArticleDistributionTrafficStat.article_id.in_(article_ids),
                ArticleDistributionTrafficStat.recorded_at >= recorded_from,
                ArticleDistributionTrafficStat.recorded_at < recorded_to,
            )
            .distinct()
            .all()
        )
        return {int(article_id) for (article_id,) in rows}

    def _overview_query(
        self,
        *,
        user_id: int | None = None,
        topic_key: str | None = None,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        project_id: int | None = None,
        theme_id: int | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        account_status: str = "active",
        publish_status: str | None = None,
        keyword: str | None = None,
        missing_traffic_only: bool = False,
        recorded_from: datetime | None = None,
        recorded_to: datetime | None = None,
    ) -> Query[ArticleDistributionArticle]:
        query = self._report_query(
            user_id=user_id,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            project_id=project_id,
            theme_id=theme_id,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
        )
        if topic_key:
            output_id = ArticleDistributionArticle.article_metadata["output_id"].as_string()
            query = query.filter(
                or_(
                    output_id == topic_key,
                    literal("article:") + cast(ArticleDistributionArticle.id, String)
                    == topic_key,
                )
            )
        if publish_status:
            query = query.filter(ArticleDistributionArticle.publish_status == publish_status)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    ArticleDistributionArticle.title.ilike(pattern),
                    ArticleDistributionArticle.keyword.ilike(pattern),
                    ArticleDistributionArticle.published_url.ilike(pattern),
                    ArticleDistributionAccount.account_name.ilike(pattern),
                    ArticleDistributionAccount.platform.ilike(pattern),
                    User.username.ilike(pattern),
                    User.email.ilike(pattern),
                    User.name.ilike(pattern),
                )
            )
        if missing_traffic_only:
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
            query = query.filter(
                ArticleDistributionArticle.publish_status == "published",
                ArticleDistributionArticle.published_url.isnot(None),
                ArticleDistributionArticle.published_url != "",
                ~recorded_in_range,
            )
        return query

    def _metadata_dashboard_identity_filter(self):
        output_id = ArticleDistributionArticle.article_metadata["output_id"].as_string()
        topic = ArticleDistributionArticle.article_metadata["topic"].as_string()
        return or_(
            output_id.isnot(None) & (output_id != ""),
            topic.isnot(None) & (topic != ""),
        )

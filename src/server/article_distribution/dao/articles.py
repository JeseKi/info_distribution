# -*- coding: utf-8 -*-
"""Article DAO methods for article distribution."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Query

from ..models import ArticleDistributionArticle, ArticleDistributionTrafficStat
from .accounts import ArticleDistributionAccountDAO


class ArticleDistributionArticleDAO(ArticleDistributionAccountDAO):
    def create_articles(
        self, articles: list[ArticleDistributionArticle]
    ) -> list[ArticleDistributionArticle]:
        self.db_session.add_all(articles)
        self.db_session.commit()
        for article in articles:
            self.db_session.refresh(article)
        return articles

    def get_article(self, article_id: int) -> ArticleDistributionArticle | None:
        return (
            self.db_session.query(ArticleDistributionArticle)
            .filter(ArticleDistributionArticle.id == article_id)
            .first()
        )

    def list_articles(
        self,
        *,
        user_id: int | None = None,
        account_id: int | None = None,
        project_id: int | None = None,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        publish_status: str | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
    ) -> list[ArticleDistributionArticle]:
        query = self._article_query(
            user_id=user_id,
            account_id=account_id,
            project_id=project_id,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            publish_status=publish_status,
            platform=platform,
            publication_type=publication_type,
        )
        if query is None:
            return []
        return (
            self._order_articles(query)
            .all()
        )

    def list_articles_page(
        self,
        *,
        user_id: int | None = None,
        account_id: int | None = None,
        project_id: int | None = None,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        publish_status: str | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[ArticleDistributionArticle], int]:
        query = self._article_query(
            user_id=user_id,
            account_id=account_id,
            project_id=project_id,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            publish_status=publish_status,
            platform=platform,
            publication_type=publication_type,
        )
        if query is None:
            return [], 0
        total = query.count()
        items = (
            self._order_articles(query)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def count_articles_by_status(
        self,
        *,
        user_id: int | None = None,
        account_id: int | None = None,
        project_id: int | None = None,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        publish_status: str | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
    ) -> dict[str, int]:
        query = self._article_query(
            user_id=user_id,
            account_id=account_id,
            project_id=project_id,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            publish_status=publish_status,
            platform=platform,
            publication_type=publication_type,
        )
        if query is None:
            return {}
        rows = (
            query.with_entities(
                ArticleDistributionArticle.publish_status,
                func.count(ArticleDistributionArticle.id),
            )
            .group_by(ArticleDistributionArticle.publish_status)
            .all()
        )
        return {str(status): int(count) for status, count in rows}

    def _article_query(
        self,
        *,
        user_id: int | None = None,
        account_id: int | None = None,
        project_id: int | None = None,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        publish_status: str | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
    ) -> Query[ArticleDistributionArticle] | None:
        query = self.db_session.query(ArticleDistributionArticle)
        if platform or publication_type:
            matching_accounts = self.list_accounts(
                user_id=user_id, platform=platform, publication_type=publication_type
            )
            matching_account_ids = [account.id for account in matching_accounts]
            if not matching_account_ids:
                return None
            query = query.filter(
                ArticleDistributionArticle.account_id.in_(matching_account_ids)
            )
        elif user_id is not None:
            query = query.filter(ArticleDistributionArticle.user_id == user_id)

        if account_id is not None:
            query = query.filter(ArticleDistributionArticle.account_id == account_id)
        if project_id is not None:
            query = query.filter(ArticleDistributionArticle.project_id == project_id)
        if scheduled_from is not None:
            query = query.filter(
                ArticleDistributionArticle.scheduled_date >= scheduled_from
            )
        if scheduled_to is not None:
            query = query.filter(
                ArticleDistributionArticle.scheduled_date <= scheduled_to
            )
        if publish_status:
            query = query.filter(
                ArticleDistributionArticle.publish_status == publish_status
            )
        return query

    def _order_articles(
        self, query: Query[ArticleDistributionArticle]
    ) -> Query[ArticleDistributionArticle]:
        return query.order_by(
            ArticleDistributionArticle.scheduled_date.desc(),
            ArticleDistributionArticle.account_id.asc(),
            ArticleDistributionArticle.id.desc(),
        )


    def update_article(
        self, article: ArticleDistributionArticle, **fields: object
    ) -> ArticleDistributionArticle:
        for key, value in fields.items():
            setattr(article, key, value)
        self.db_session.commit()
        self.db_session.refresh(article)
        return article

    def delete_article(self, article: ArticleDistributionArticle) -> None:
        self.db_session.query(ArticleDistributionTrafficStat).filter(
            ArticleDistributionTrafficStat.article_id == article.id
        ).delete(synchronize_session=False)
        self.db_session.delete(article)
        self.db_session.commit()

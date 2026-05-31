# -*- coding: utf-8 -*-
"""Article distribution DAO."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import case, func
from sqlalchemy.orm import Query
from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO
from src.server.auth.models import User

from .models import (
    ArticleDistributionAPIKey,
    ArticleDistributionAccount,
    ArticleDistributionArticle,
    ArticleDistributionTrafficStat,
)


class ArticleDistributionDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def get_account(self, account_id: int) -> ArticleDistributionAccount | None:
        return (
            self.db_session.query(ArticleDistributionAccount)
            .filter(ArticleDistributionAccount.id == account_id)
            .first()
        )

    def list_accounts(
        self,
        *,
        user_id: int | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
        is_active: bool | None = None,
    ) -> list[ArticleDistributionAccount]:
        query = self.db_session.query(ArticleDistributionAccount)
        if user_id is not None:
            query = query.filter(ArticleDistributionAccount.user_id == user_id)
        if platform:
            query = query.filter(ArticleDistributionAccount.platform == platform)
        if publication_type:
            query = query.filter(
                ArticleDistributionAccount.publication_type == publication_type
            )
        if is_active is not None:
            query = query.filter(ArticleDistributionAccount.is_active.is_(is_active))
        return (
            query.order_by(
                ArticleDistributionAccount.platform.asc(),
                ArticleDistributionAccount.account_name.asc(),
                ArticleDistributionAccount.id.asc(),
            )
            .all()
        )

    def list_account_owner_rows(
        self, *, is_active: bool | None = None
    ) -> list[tuple[ArticleDistributionAccount, User]]:
        query = (
            self.db_session.query(ArticleDistributionAccount, User)
            .join(User, ArticleDistributionAccount.user_id == User.id)
        )
        if is_active is not None:
            query = query.filter(ArticleDistributionAccount.is_active.is_(is_active))
        rows = query.order_by(
            User.id.asc(),
            ArticleDistributionAccount.platform.asc(),
            ArticleDistributionAccount.account_name.asc(),
            ArticleDistributionAccount.publication_type.asc(),
            ArticleDistributionAccount.id.asc(),
        ).all()
        return [(account, owner) for account, owner in rows]

    def create_account(
        self, account: ArticleDistributionAccount
    ) -> ArticleDistributionAccount:
        self.db_session.add(account)
        self.db_session.commit()
        self.db_session.refresh(account)
        return account

    def update_account(
        self, account: ArticleDistributionAccount, **fields: object
    ) -> ArticleDistributionAccount:
        for key, value in fields.items():
            setattr(account, key, value)
        self.db_session.commit()
        self.db_session.refresh(account)
        return account

    def delete_account(self, account: ArticleDistributionAccount) -> None:
        self.db_session.delete(account)
        self.db_session.commit()

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
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        publish_status: str | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
    ) -> list[ArticleDistributionArticle]:
        query = self._article_query(
            user_id=user_id,
            account_id=account_id,
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
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        publish_status: str | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
    ) -> dict[str, int]:
        query = self._article_query(
            user_id=user_id,
            account_id=account_id,
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

    def create_api_key(
        self, api_key: ArticleDistributionAPIKey
    ) -> ArticleDistributionAPIKey:
        self.db_session.add(api_key)
        self.db_session.commit()
        self.db_session.refresh(api_key)
        return api_key

    def list_api_keys(self) -> list[ArticleDistributionAPIKey]:
        return (
            self.db_session.query(ArticleDistributionAPIKey)
            .order_by(ArticleDistributionAPIKey.created_at.desc())
            .all()
        )

    def get_api_key(self, api_key_id: int) -> ArticleDistributionAPIKey | None:
        return (
            self.db_session.query(ArticleDistributionAPIKey)
            .filter(ArticleDistributionAPIKey.id == api_key_id)
            .first()
        )

    def find_active_api_key(
        self, *, key_hash: str, key_prefix: str
    ) -> ArticleDistributionAPIKey | None:
        return (
            self.db_session.query(ArticleDistributionAPIKey)
            .filter(
                ArticleDistributionAPIKey.key_hash == key_hash,
                ArticleDistributionAPIKey.key_prefix == key_prefix,
                ArticleDistributionAPIKey.is_active.is_(True),
                ArticleDistributionAPIKey.revoked_at.is_(None),
            )
            .first()
        )

    def mark_api_key_used(
        self, api_key: ArticleDistributionAPIKey, used_at: datetime
    ) -> ArticleDistributionAPIKey:
        api_key.last_used_at = used_at
        self.db_session.commit()
        self.db_session.refresh(api_key)
        return api_key

    def revoke_api_key(
        self, api_key: ArticleDistributionAPIKey, revoked_at: datetime
    ) -> ArticleDistributionAPIKey:
        api_key.is_active = False
        api_key.revoked_at = revoked_at
        self.db_session.commit()
        self.db_session.refresh(api_key)
        return api_key

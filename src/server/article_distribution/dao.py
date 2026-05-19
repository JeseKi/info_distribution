# -*- coding: utf-8 -*-
"""Article distribution DAO."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO
from src.server.auth.models import User

from .models import (
    ArticleDistributionAPIKey,
    ArticleDistributionAccount,
    ArticleDistributionArticle,
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
        return (
            query.order_by(
                ArticleDistributionAccount.platform.asc(),
                ArticleDistributionAccount.account_name.asc(),
                ArticleDistributionAccount.id.asc(),
            )
            .all()
        )

    def list_account_owner_rows(self) -> list[tuple[ArticleDistributionAccount, User]]:
        rows = (
            self.db_session.query(ArticleDistributionAccount, User)
            .join(User, ArticleDistributionAccount.user_id == User.id)
            .order_by(
                User.id.asc(),
                ArticleDistributionAccount.platform.asc(),
                ArticleDistributionAccount.account_name.asc(),
                ArticleDistributionAccount.publication_type.asc(),
                ArticleDistributionAccount.id.asc(),
            )
            .all()
        )
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
        query = self.db_session.query(ArticleDistributionArticle)
        if platform or publication_type:
            matching_accounts = self.list_accounts(
                user_id=user_id, platform=platform, publication_type=publication_type
            )
            matching_account_ids = [account.id for account in matching_accounts]
            if not matching_account_ids:
                return []
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
        return (
            query.order_by(
                ArticleDistributionArticle.scheduled_date.desc(),
                ArticleDistributionArticle.account_id.asc(),
                ArticleDistributionArticle.id.desc(),
            )
            .all()
        )

    def list_report_article_owner_rows(
        self,
        *,
        scheduled_from: date | None = None,
        scheduled_to: date | None = None,
        platform: str | None = None,
        publication_type: str | None = None,
    ) -> list[
        tuple[ArticleDistributionArticle, ArticleDistributionAccount, User]
    ]:
        query = (
            self.db_session.query(
                ArticleDistributionArticle,
                ArticleDistributionAccount,
                User,
            )
            .join(
                ArticleDistributionAccount,
                ArticleDistributionArticle.account_id
                == ArticleDistributionAccount.id,
            )
            .join(User, ArticleDistributionArticle.user_id == User.id)
        )
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
        rows = (
            query.order_by(
                User.id.asc(),
                ArticleDistributionArticle.scheduled_date.asc(),
                ArticleDistributionArticle.id.asc(),
            )
            .all()
        )
        return [(article, account, owner) for article, account, owner in rows]

    def update_article(
        self, article: ArticleDistributionArticle, **fields: object
    ) -> ArticleDistributionArticle:
        for key, value in fields.items():
            setattr(article, key, value)
        self.db_session.commit()
        self.db_session.refresh(article)
        return article

    def delete_article(self, article: ArticleDistributionArticle) -> None:
        self.db_session.delete(article)
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

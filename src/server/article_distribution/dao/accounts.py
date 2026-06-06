# -*- coding: utf-8 -*-
"""Account DAO methods for article distribution."""

from __future__ import annotations

from src.server.auth.models import User

from ..models import ArticleDistributionAccount
from .base import ArticleDistributionBaseDAO


class ArticleDistributionAccountDAO(ArticleDistributionBaseDAO):
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

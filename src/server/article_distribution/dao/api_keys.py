# -*- coding: utf-8 -*-
"""API key DAO methods for article distribution."""

from __future__ import annotations

from datetime import datetime

from ..models import ArticleDistributionAPIKey
from .base import ArticleDistributionBaseDAO


class ArticleDistributionAPIKeyDAO(ArticleDistributionBaseDAO):
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

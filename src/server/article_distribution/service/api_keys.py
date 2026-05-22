# -*- coding: utf-8 -*-
"""API key service functions for article distribution."""

from __future__ import annotations

import hmac
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth.models import User

from ..dao import ArticleDistributionDAO
from ..models import ArticleDistributionAPIKey
from .helpers import (
    API_KEY_PREFIX,
    API_KEY_PREFIX_LENGTH,
    assert_admin,
    generate_api_key,
    hash_api_key,
    normalize_required,
)


def list_api_keys(db: Session, *, current_user: User) -> list[ArticleDistributionAPIKey]:
    assert_admin(current_user)
    return ArticleDistributionDAO(db).list_api_keys()


def create_api_key(
    db: Session, *, name: str, current_user: User
) -> tuple[ArticleDistributionAPIKey, str]:
    assert_admin(current_user)
    normalized_name = normalize_required(name, "API Key 名称不能为空")
    raw_key = generate_api_key()
    api_key = ArticleDistributionAPIKey(
        name=normalized_name,
        key_prefix=raw_key[:API_KEY_PREFIX_LENGTH],
        key_hash=hash_api_key(raw_key),
        created_by_user_id=current_user.id,
        is_active=True,
    )
    created = ArticleDistributionDAO(db).create_api_key(api_key)
    return created, raw_key


def revoke_api_key(
    db: Session, *, api_key_id: int, current_user: User
) -> ArticleDistributionAPIKey:
    assert_admin(current_user)
    dao = ArticleDistributionDAO(db)
    api_key = dao.get_api_key(api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key 不存在")
    if not api_key.is_active:
        return api_key
    return dao.revoke_api_key(api_key, datetime.now(timezone.utc))


def authenticate_api_key(db: Session, raw_key: str | None) -> ArticleDistributionAPIKey:
    normalized = raw_key.strip() if isinstance(raw_key, str) else ""
    if not normalized:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少 API Key")
    if not normalized.startswith(f"{API_KEY_PREFIX}_"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key 无效")

    key_hash = hash_api_key(normalized)
    key_prefix = normalized[:API_KEY_PREFIX_LENGTH]
    dao = ArticleDistributionDAO(db)
    api_key = dao.find_active_api_key(key_hash=key_hash, key_prefix=key_prefix)
    if api_key is None or not hmac.compare_digest(api_key.key_hash, key_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key 无效")
    return dao.mark_api_key_used(api_key, datetime.now(timezone.utc))

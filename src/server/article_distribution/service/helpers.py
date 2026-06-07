# -*- coding: utf-8 -*-
"""Shared helpers for article distribution services."""

from __future__ import annotations

import hashlib
import secrets
from urllib.parse import urlparse

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.auth.schemas import UserRole
from src.server.project_management.dao import ProjectManagementDAO
from src.server.project_management.schemas import ProjectSummary

from ..dao import ArticleDistributionDAO
from ..models import ArticleDistributionAccount, ArticleDistributionArticle
from ..schemas import ArticleOut, PublishStatus, PublicationType

API_KEY_PREFIX = "adv1"
API_KEY_PREFIX_LENGTH = 16


def get_accessible_account(
    db: Session, account_id: int, current_user: User, *, write: bool
) -> ArticleDistributionAccount:
    account = get_account_or_404(db, account_id)
    if current_user.role == UserRole.ADMIN:
        return account
    if account.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    return account


def get_account_or_404(db: Session, account_id: int) -> ArticleDistributionAccount:
    account = ArticleDistributionDAO(db).get_account(account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
    return account


def get_active_account_or_404(
    db: Session, account_id: int
) -> ArticleDistributionAccount:
    account = get_account_or_404(db, account_id)
    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号已停用，不能新增文章",
        )
    return account


def get_accessible_article(
    db: Session, article_id: int, current_user: User
) -> ArticleDistributionArticle:
    article = ArticleDistributionDAO(db).get_article(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    if current_user.role == UserRole.ADMIN or article.user_id == current_user.id:
        return article
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")


def resolve_target_user_id(current_user: User, requested_user_id: int | None) -> int:
    if requested_user_id is None:
        return current_user.id
    if current_user.role == UserRole.ADMIN:
        return requested_user_id
    if requested_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    return current_user.id


def resolve_optional_target_user_id(
    current_user: User, requested_user_id: int | None
) -> int | None:
    if requested_user_id is None and current_user.role == UserRole.ADMIN:
        return None
    return resolve_target_user_id(current_user, requested_user_id)


def assert_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")


def articles_to_out(
    db: Session, articles: list[ArticleDistributionArticle]
) -> list[ArticleOut]:
    return [article_to_out(db, article) for article in articles]


def article_to_out(db: Session, article: ArticleDistributionArticle) -> ArticleOut:
    account = ArticleDistributionDAO(db).get_account(article.account_id)
    project = ProjectManagementDAO(db).get_project(article.project_id)
    return ArticleOut.model_validate(
        {
            **article.__dict__,
            "metadata": article.article_metadata,
            "account": account,
            "project": ProjectSummary.model_validate(project) if project else None,
        }
    )


def normalize_required(value: str, error_message: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    return normalized


def normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def normalize_publication_type(value: str) -> PublicationType:
    if value == "video":
        return "video"
    if value == "article":
        return "article"
    if value == "image_text":
        return "image_text"
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="账号发布类型无效",
    )


def normalize_publish_status(value: str) -> PublishStatus:
    if value == "unpublished":
        return "unpublished"
    if value == "published":
        return "published"
    if value == "invalid":
        return "invalid"
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="文章发布状态无效",
    )


def status_update_fields(
    publish_status: str, published_url: str | None
) -> dict[str, str | None]:
    normalized_status = normalize_publish_status(publish_status)
    if normalized_status == "published":
        return {
            "publish_status": normalized_status,
            "published_url": normalize_published_url(published_url),
        }
    return {"publish_status": normalized_status, "published_url": None}


def normalize_published_url(value: str | None) -> str:
    normalized = normalize_optional(value)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="标记已发布时必须填写发布地址",
        )
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="发布地址必须是 http 或 https URL",
        )
    return normalized


def generate_api_key() -> str:
    return f"{API_KEY_PREFIX}_{secrets.token_urlsafe(32)}"


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

# -*- coding: utf-8 -*-
"""Article query service functions for article distribution."""

from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth.models import User

from ..dao import ArticleDistributionDAO
from ..schemas import ArticleOut, ArticlePageOut, ArticleStatusCountsOut
from .helpers import (
    article_to_out,
    articles_to_out,
    get_accessible_account,
    get_accessible_article,
    normalize_optional,
    resolve_optional_target_user_id,
)


def list_articles(
    db: Session,
    *,
    current_user: User,
    user_id: int | None = None,
    account_id: int | None = None,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    publish_status: str | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
) -> list[ArticleOut]:
    target_user_id = resolve_optional_target_user_id(current_user, user_id)
    if account_id is not None:
        account = get_accessible_account(db, account_id, current_user, write=False)
        if target_user_id is not None and account.user_id != target_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    dao = ArticleDistributionDAO(db)
    articles = dao.list_articles(
        user_id=target_user_id,
        account_id=account_id,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publish_status=publish_status,
        platform=normalize_optional(platform),
        publication_type=publication_type,
    )
    return articles_to_out(db, articles)


def list_articles_page(
    db: Session,
    *,
    current_user: User,
    user_id: int | None = None,
    account_id: int | None = None,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    publish_status: str | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> ArticlePageOut:
    target_user_id = resolve_optional_target_user_id(current_user, user_id)
    if account_id is not None:
        account = get_accessible_account(db, account_id, current_user, write=False)
        if target_user_id is not None and account.user_id != target_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    dao = ArticleDistributionDAO(db)
    normalized_platform = normalize_optional(platform)
    articles, total = dao.list_articles_page(
        user_id=target_user_id,
        account_id=account_id,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publish_status=publish_status,
        platform=normalized_platform,
        publication_type=publication_type,
        page=page,
        page_size=page_size,
    )
    status_counts = dao.count_articles_by_status(
        user_id=target_user_id,
        account_id=account_id,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publish_status=publish_status,
        platform=normalized_platform,
        publication_type=publication_type,
    )
    return ArticlePageOut(
        items=articles_to_out(db, articles),
        total=total,
        page=page,
        page_size=page_size,
        status_counts=ArticleStatusCountsOut(
            unpublished=status_counts.get("unpublished", 0),
            published=status_counts.get("published", 0),
            invalid=status_counts.get("invalid", 0),
        ),
    )


def get_article(db: Session, *, article_id: int, current_user: User) -> ArticleOut:
    article = get_accessible_article(db, article_id, current_user)
    return article_to_out(db, article)

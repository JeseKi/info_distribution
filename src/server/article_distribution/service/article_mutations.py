# -*- coding: utf-8 -*-
"""Article mutation service functions for article distribution."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth.models import User

from ..dao import ArticleDistributionDAO
from ..models import ArticleDistributionAPIKey
from ..schemas import ArticleBatchCreate, ArticleOut, ArticleUpdate, ArticleV1Update
from .article_builders import build_articles, v1_update_fields
from .helpers import (
    article_to_out,
    articles_to_out,
    assert_admin,
    get_accessible_article,
    get_active_account_or_404,
    normalize_published_url,
    normalize_required,
    status_update_fields,
)


def update_article_status(
    db: Session,
    *,
    article_id: int,
    publish_status: str,
    published_url: str | None,
    current_user: User,
) -> ArticleOut:
    article = get_accessible_article(db, article_id, current_user)
    fields = status_update_fields(publish_status, published_url)
    updated = ArticleDistributionDAO(db).update_article(
        article,
        **fields,
    )
    return article_to_out(db, updated)


def update_article_as_admin(
    db: Session, *, article_id: int, payload: ArticleUpdate, current_user: User
) -> ArticleOut:
    assert_admin(current_user)
    dao = ArticleDistributionDAO(db)
    article = dao.get_article(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    fields = payload.model_dump(exclude_unset=True)
    if "metadata" in fields:
        fields["article_metadata"] = fields.pop("metadata")
    if "account_id" in fields and fields["account_id"] is not None:
        account = get_active_account_or_404(db, int(fields["account_id"]))
        fields["account_id"] = account.id
        fields["user_id"] = account.user_id
    if "title" in fields and fields["title"] is not None:
        fields["title"] = normalize_required(str(fields["title"]), "标题不能为空")
    if "markdown_content" in fields and fields["markdown_content"] is not None:
        fields["markdown_content"] = normalize_required(
            str(fields["markdown_content"]), "正文不能为空"
        )
    if "publish_status" in fields:
        status_value = fields.pop("publish_status")
        published_url = fields.pop("published_url", None)
        if status_value is not None:
            fields.update(status_update_fields(str(status_value), published_url))
    elif "published_url" in fields:
        published_url = fields.pop("published_url")
        if article.publish_status == "published":
            fields["published_url"] = normalize_published_url(published_url)

    updated = dao.update_article(article, **fields)
    return article_to_out(db, updated)


def update_article_with_api_key(
    db: Session,
    *,
    article_id: int,
    payload: ArticleV1Update,
    api_key: ArticleDistributionAPIKey,
) -> ArticleOut:
    _ = api_key
    dao = ArticleDistributionDAO(db)
    article = dao.get_article(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    fields = v1_update_fields(db, article=article, payload=payload)
    if not fields:
        return article_to_out(db, article)

    updated = dao.update_article(article, **fields)
    return article_to_out(db, updated)


def delete_article_as_admin(db: Session, *, article_id: int, current_user: User) -> None:
    assert_admin(current_user)
    dao = ArticleDistributionDAO(db)
    article = dao.get_article(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    dao.delete_article(article)


def create_articles_as_admin(
    db: Session, *, payload: ArticleBatchCreate, current_user: User
) -> list[ArticleOut]:
    assert_admin(current_user)
    account = get_active_account_or_404(db, payload.account_id)
    articles = build_articles(
        account=account,
        items=payload.articles,
        source="admin",
        created_by_user_id=current_user.id,
        api_key_id=None,
    )
    created = ArticleDistributionDAO(db).create_articles(articles)
    return articles_to_out(db, created)


def create_articles_with_api_key(
    db: Session,
    *,
    payload: ArticleBatchCreate,
    api_key: ArticleDistributionAPIKey,
) -> list[ArticleOut]:
    account = get_active_account_or_404(db, payload.account_id)
    articles = build_articles(
        account=account,
        items=payload.articles,
        source="api",
        created_by_user_id=api_key.created_by_user_id,
        api_key_id=api_key.id,
    )
    created = ArticleDistributionDAO(db).create_articles(articles)
    return articles_to_out(db, created)

# -*- coding: utf-8 -*-
"""Article service functions for article distribution."""

from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth.models import User

from ..dao import ArticleDistributionDAO
from ..models import (
    ArticleDistributionAPIKey,
    ArticleDistributionAccount,
    ArticleDistributionArticle,
)
from ..schemas import (
    ArticleBatchCreate,
    ArticleOut,
    ArticlePageOut,
    ArticleStatusCountsOut,
    ArticleUpdate,
    ArticleV1Update,
    ArticleUploadItem,
)
from .helpers import (
    article_to_out,
    articles_to_out,
    assert_admin,
    get_accessible_account,
    get_accessible_article,
    get_active_account_or_404,
    normalize_optional,
    normalize_published_url,
    normalize_required,
    resolve_optional_target_user_id,
    status_update_fields,
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

    fields = _v1_update_fields(db, article=article, payload=payload)
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
    articles = _build_articles(
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
    articles = _build_articles(
        account=account,
        items=payload.articles,
        source="api",
        created_by_user_id=api_key.created_by_user_id,
        api_key_id=api_key.id,
    )
    created = ArticleDistributionDAO(db).create_articles(articles)
    return articles_to_out(db, created)


def _build_articles(
    *,
    account: ArticleDistributionAccount,
    items: list[ArticleUploadItem],
    source: str,
    created_by_user_id: int | None,
    api_key_id: int | None,
) -> list[ArticleDistributionArticle]:
    return [
        ArticleDistributionArticle(
            user_id=account.user_id,
            account_id=account.id,
            title=normalize_required(item.title, "标题不能为空"),
            markdown_content=normalize_required(item.markdown_content, "正文不能为空"),
            article_metadata=item.metadata,
            scheduled_date=item.scheduled_date,
            publish_status="unpublished",
            source=source,
            created_by_user_id=created_by_user_id,
            api_key_id=api_key_id,
        )
        for item in items
    ]


def _v1_update_fields(
    db: Session,
    *,
    article: ArticleDistributionArticle,
    payload: ArticleV1Update,
) -> dict[str, object]:
    raw_fields = payload.model_dump(exclude_unset=True)
    fields: dict[str, object] = {}

    account_id = raw_fields.get("account_id")
    if account_id is not None:
        account = get_active_account_or_404(db, int(account_id))
        fields["account_id"] = account.id
        fields["user_id"] = account.user_id

    title = _non_empty_string(raw_fields.get("title"))
    if title is not None:
        fields["title"] = title

    markdown_content = _non_empty_string(raw_fields.get("markdown_content"))
    if markdown_content is not None:
        fields["markdown_content"] = markdown_content

    if raw_fields.get("scheduled_date") is not None:
        fields["scheduled_date"] = raw_fields["scheduled_date"]

    metadata = raw_fields.get("metadata")
    if isinstance(metadata, dict) and metadata:
        fields["article_metadata"] = metadata

    if "publish_status" in raw_fields and raw_fields["publish_status"] is not None:
        publish_status = str(raw_fields["publish_status"])
        published_url = _non_empty_string(raw_fields.get("published_url"))
        if publish_status == "published" and published_url is None:
            published_url = article.published_url
        fields.update(status_update_fields(publish_status, published_url))
    else:
        published_url = _non_empty_string(raw_fields.get("published_url"))
        if published_url is not None and article.publish_status == "published":
            fields["published_url"] = normalize_published_url(published_url)

    return fields


def _non_empty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None

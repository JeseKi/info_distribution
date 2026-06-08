# -*- coding: utf-8 -*-
"""Article mutation service functions for article distribution."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.project_management.dao import ProjectManagementDAO
from src.server.project_management.service import (
    validate_user_project_id,
    validate_user_project_theme_id,
)

from ..dao import ArticleDistributionDAO
from ..models import ArticleDistributionAPIKey, ArticleDistributionAccount
from ..schemas import (
    ArticleBatchCreate,
    ArticleOut,
    ArticleUpdate,
    ArticleV1Update,
    ArticleV2BatchCreate,
    ArticleV2Update,
)
from .article_builders import (
    build_articles,
    build_v2_articles,
    v1_update_fields,
    v2_update_fields,
)
from .helpers import (
    article_to_out,
    articles_to_out,
    assert_admin,
    get_accessible_article,
    get_account_or_404,
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
    target_user_id = article.user_id
    next_project_id = fields.get("project_id", article.project_id)
    if "account_id" in fields and fields["account_id"] is not None:
        account = get_active_account_or_404(db, int(fields["account_id"]))
        fields["account_id"] = account.id
        fields["user_id"] = account.user_id
        target_user_id = account.user_id
    else:
        account = get_account_or_404(db, article.account_id)
    if next_project_id is not None:
        fields["project_id"] = validate_user_project_id(
            db, target_user_id, int(next_project_id)
        )
        _assert_article_project_matches_account_theme(
            db, int(fields["project_id"]), account
        )
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


def update_article_with_api_key_v2(
    db: Session,
    *,
    article_id: int,
    payload: ArticleV2Update,
    api_key: ArticleDistributionAPIKey,
) -> ArticleOut:
    _ = api_key
    dao = ArticleDistributionDAO(db)
    article = dao.get_article(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    fields = v2_update_fields(db, article=article, payload=payload)
    if not fields:
        return article_to_out(db, article)

    target_user_value = fields.get("user_id")
    target_user_id = (
        target_user_value if isinstance(target_user_value, int) else article.user_id
    )
    account_id = fields.get("account_id")
    account = (
        get_active_account_or_404(db, account_id)
        if isinstance(account_id, int)
        else get_account_or_404(db, article.account_id)
    )
    project_value = fields.get("project_id")
    next_project_id = (
        project_value if isinstance(project_value, int) else article.project_id
    )
    validated_project_id = validate_user_project_id(
        db, target_user_id, next_project_id
    )
    fields["project_id"] = validated_project_id
    _assert_article_project_matches_account_theme(
        db, validated_project_id, account
    )

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
    for item in payload.articles:
        validate_user_project_id(db, account.user_id, item.project_id)
        _assert_article_project_matches_account_theme(db, item.project_id, account)
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
    for item in payload.articles:
        validate_user_project_id(db, account.user_id, item.project_id)
        _assert_article_project_matches_account_theme(db, item.project_id, account)
    articles = build_articles(
        account=account,
        items=payload.articles,
        source="api",
        created_by_user_id=api_key.created_by_user_id,
        api_key_id=api_key.id,
    )
    created = ArticleDistributionDAO(db).create_articles(articles)
    return articles_to_out(db, created)


def _assert_article_project_matches_account_theme(
    db: Session, project_id: int, account: ArticleDistributionAccount
) -> None:
    validate_user_project_theme_id(db, account.user_id, project_id, account.theme_id)


def create_articles_with_api_key_v2(
    db: Session,
    *,
    payload: ArticleV2BatchCreate,
    api_key: ArticleDistributionAPIKey,
) -> list[ArticleOut]:
    account = get_active_account_or_404(db, payload.account_id)
    for item in payload.articles:
        if item.theme_id != account.theme_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文章主题必须与账号主题一致",
            )
    project_id = _resolve_v2_article_project_id(db, account)
    articles = build_v2_articles(
        account=account,
        items=payload.articles,
        project_id=project_id,
        source="api",
        created_by_user_id=api_key.created_by_user_id,
        api_key_id=api_key.id,
    )
    created = ArticleDistributionDAO(db).create_articles(articles)
    return articles_to_out(db, created)


def _resolve_v2_article_project_id(
    db: Session, account: ArticleDistributionAccount
) -> int:
    dao = ProjectManagementDAO(db)
    projects = [
        project
        for project in dao.list_user_projects(account.user_id)
        if project.is_active
        and account.theme_id in set(dao.list_project_theme_ids(project.id))
    ]
    if len(projects) == 1:
        return projects[0].id
    if not projects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号主题没有可用项目",
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="账号主题关联多个项目，无法自动确定文章项目",
    )

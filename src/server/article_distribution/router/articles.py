# -*- coding: utf-8 -*-
"""Article routes for article distribution."""

from __future__ import annotations

from datetime import date

from fastapi import Depends, Query, Security, status
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import (
    SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE,
    SCOPE_ARTICLE_DISTRIBUTION_READ,
    SCOPE_ARTICLE_DISTRIBUTION_WRITE,
)
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from .. import service
from ..schemas import (
    ArticleOut,
    ArticlePageOut,
    ArticleStatusUpdate,
    ArticleUpdate,
    PublishStatus,
    PublicationType,
)
from .shared import admin_router, router


@router.get("/articles", response_model=list[ArticleOut], summary="列出文章")
async def list_articles(
    user_id: int | None = Query(default=None, ge=1),
    account_id: int | None = Query(default=None, ge=1),
    project_id: int | None = Query(default=None, ge=1),
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    publish_status: PublishStatus | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_READ]
    ),
):
    def _list():
        return service.list_articles(
            db,
            current_user=current_user,
            user_id=user_id,
            account_id=account_id,
            project_id=project_id,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            publish_status=publish_status,
            platform=platform,
            publication_type=publication_type,
        )

    return await run_in_thread(_list)


@router.get("/articles/page", response_model=ArticlePageOut, summary="分页列出文章")
async def list_articles_page(
    user_id: int | None = Query(default=None, ge=1),
    account_id: int | None = Query(default=None, ge=1),
    project_id: int | None = Query(default=None, ge=1),
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    publish_status: PublishStatus | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_READ]
    ),
):
    def _list():
        return service.list_articles_page(
            db,
            current_user=current_user,
            user_id=user_id,
            account_id=account_id,
            project_id=project_id,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            publish_status=publish_status,
            platform=platform,
            publication_type=publication_type,
            page=page,
            page_size=page_size,
        )

    return await run_in_thread(_list)


@router.get("/articles/{article_id}", response_model=ArticleOut, summary="获取文章")
async def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_READ]
    ),
):
    def _get():
        return service.get_article(db, article_id=article_id, current_user=current_user)

    return await run_in_thread(_get)


@router.patch(
    "/articles/{article_id}/status",
    response_model=ArticleOut,
    summary="更新文章发布状态",
)
async def update_article_status(
    article_id: int,
    payload: ArticleStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _update():
        return service.update_article_status(
            db,
            article_id=article_id,
            publish_status=payload.publish_status,
            published_url=payload.published_url,
            current_user=current_user,
        )

    return await run_in_thread(_update)


@admin_router.patch(
    "/articles/{article_id}",
    response_model=ArticleOut,
    summary="管理员更新文章",
)
async def update_article_as_admin(
    article_id: int,
    payload: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _update():
        return service.update_article_as_admin(
            db, article_id=article_id, payload=payload, current_user=current_user
        )

    return await run_in_thread(_update)


@admin_router.delete(
    "/articles/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="管理员删除文章",
)
async def delete_article_as_admin(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _delete():
        service.delete_article_as_admin(
            db, article_id=article_id, current_user=current_user
        )

    return await run_in_thread(_delete)

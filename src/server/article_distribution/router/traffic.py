# -*- coding: utf-8 -*-
"""Traffic statistic routes for article distribution."""

from __future__ import annotations

from datetime import date

from fastapi import Depends, Query, Security, status
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import (
    SCOPE_ARTICLE_DISTRIBUTION_READ,
    SCOPE_ARTICLE_DISTRIBUTION_WRITE,
)
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from .. import service
from ..schemas import (
    ArticleTrafficStatCreate,
    ArticleTrafficStatOut,
    ArticleTrafficSummaryPageOut,
    PublishStatus,
    PublicationType,
)
from .shared import router


@router.get(
    "/traffic-stats/articles/page",
    response_model=ArticleTrafficSummaryPageOut,
    summary="分页列出文章流量统计",
)
async def list_article_traffic_summaries(
    user_id: int | None = Query(default=None, ge=1),
    account_id: int | None = Query(default=None, ge=1),
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
        return service.list_article_traffic_summaries(
            db,
            current_user=current_user,
            user_id=user_id,
            account_id=account_id,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            publish_status=publish_status,
            platform=platform,
            publication_type=publication_type,
            page=page,
            page_size=page_size,
        )

    return await run_in_thread(_list)


@router.get(
    "/articles/{article_id}/traffic-stats",
    response_model=list[ArticleTrafficStatOut],
    summary="列出文章流量统计记录",
)
async def list_article_traffic_stats(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_READ]
    ),
):
    def _list():
        return service.list_article_traffic_stats(
            db, article_id=article_id, current_user=current_user
        )

    return await run_in_thread(_list)


@router.post(
    "/articles/{article_id}/traffic-stats",
    response_model=ArticleTrafficStatOut,
    status_code=status.HTTP_201_CREATED,
    summary="新增文章流量统计记录",
)
async def create_article_traffic_stat(
    article_id: int,
    payload: ArticleTrafficStatCreate,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _create():
        return service.create_article_traffic_stat(
            db, article_id=article_id, payload=payload, current_user=current_user
        )

    return await run_in_thread(_create)


@router.delete(
    "/traffic-stats/{stat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除文章流量统计记录",
)
async def delete_article_traffic_stat(
    stat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _delete():
        service.delete_article_traffic_stat(
            db, stat_id=stat_id, current_user=current_user
        )

    return await run_in_thread(_delete)

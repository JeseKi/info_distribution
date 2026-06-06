# -*- coding: utf-8 -*-
"""Overview report routes for article distribution."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from fastapi import Depends, HTTPException, Query, Response, Security, status
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import (
    SCOPE_ARTICLE_DISTRIBUTION_METADATA_DASHBOARD_READ,
    SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ,
)
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from .. import service
from ..schemas import (
    AccountStatusFilter,
    ArticleDistributionOverviewArticleDetailOut,
    ArticleDistributionOverviewArticlePageOut,
    ArticleDistributionOverviewOut,
    ArticleDistributionOverviewView,
    PublishStatus,
    PublicationType,
)
from .shared import router


OverviewExportFormat = Literal["csv", "xlsx"]


def _ensure_overview_view_allowed(
    *, view: ArticleDistributionOverviewView, current_user: User
) -> None:
    if (
        view == "topics"
        and SCOPE_ARTICLE_DISTRIBUTION_METADATA_DASHBOARD_READ
        not in current_user.effective_scopes
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="缺少 article_distribution:metadata_dashboard:read 权限",
        )


@router.get(
    "/reports/overview",
    response_model=ArticleDistributionOverviewOut,
    summary="查看统一分发报表",
)
async def list_report_overview(
    view: ArticleDistributionOverviewView = Query(default="users"),
    keyword: str | None = Query(default=None),
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    account_status: AccountStatusFilter = Query(default="active"),
    publish_status: PublishStatus | None = Query(default=None),
    missing_traffic_only: bool = Query(default=False),
    recorded_from: datetime | None = Query(default=None),
    recorded_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ]
    ),
):
    _ensure_overview_view_allowed(view=view, current_user=current_user)

    def _list():
        return service.list_report_overview(
            db,
            view=view,
            keyword=keyword,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
            publish_status=publish_status,
            missing_traffic_only=missing_traffic_only,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
            page=page,
            page_size=page_size,
        )

    return await run_in_thread(_list)


@router.get(
    "/reports/overview/articles",
    response_model=ArticleDistributionOverviewArticlePageOut,
    summary="查看统一分发报表文章明细",
)
async def list_report_overview_articles(
    user_id: int | None = Query(default=None, ge=1),
    topic_key: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    account_status: AccountStatusFilter = Query(default="active"),
    publish_status: PublishStatus | None = Query(default=None),
    missing_traffic_only: bool = Query(default=False),
    recorded_from: datetime | None = Query(default=None),
    recorded_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ]
    ),
):
    def _list():
        return service.list_report_overview_articles(
            db,
            user_id=user_id,
            topic_key=topic_key,
            keyword=keyword,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
            publish_status=publish_status,
            missing_traffic_only=missing_traffic_only,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
            page=page,
            page_size=page_size,
        )

    return await run_in_thread(_list)


@router.get(
    "/reports/overview/articles/{article_id}",
    response_model=ArticleDistributionOverviewArticleDetailOut,
    summary="查看统一分发报表文章详情",
)
async def get_report_overview_article_detail(
    article_id: int,
    recorded_from: datetime | None = Query(default=None),
    recorded_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ]
    ),
):
    def _get():
        return service.get_report_overview_article_detail(
            db,
            article_id=article_id,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
        )

    return await run_in_thread(_get)


@router.get(
    "/reports/overview/export",
    summary="导出统一分发报表",
)
async def export_report_overview(
    view: ArticleDistributionOverviewView = Query(default="users"),
    export_format: OverviewExportFormat = Query(default="xlsx", alias="format"),
    keyword: str | None = Query(default=None),
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    account_status: AccountStatusFilter = Query(default="active"),
    publish_status: PublishStatus | None = Query(default=None),
    missing_traffic_only: bool = Query(default=False),
    recorded_from: datetime | None = Query(default=None),
    recorded_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ]
    ),
):
    _ensure_overview_view_allowed(view=view, current_user=current_user)

    def _export():
        return service.build_report_overview_export(
            db,
            export_format=export_format,
            view=view,
            keyword=keyword,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
            publish_status=publish_status,
            missing_traffic_only=missing_traffic_only,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
        )

    content = await run_in_thread(_export)
    filename_date = (scheduled_to or date.today()).isoformat()
    extension = service.EXPORT_FILE_EXTENSIONS[export_format]
    return Response(
        content=content,
        media_type=service.EXPORT_MEDIA_TYPES[export_format],
        headers={
            "Content-Disposition": (
                f'attachment; filename="overview-{view}-{filename_date}.{extension}"'
            ),
        },
    )

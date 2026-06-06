# -*- coding: utf-8 -*-
"""Report routes for article distribution."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import Depends, HTTPException, Query, Security, status
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
    ArticleDistributionMissingTrafficPageOut,
    ArticleDistributionMissingTrafficReportOut,
    ArticleDistributionMissingTrafficUserOut,
    ArticleDistributionMetadataDashboardOut,
    ArticleDistributionOverviewOut,
    ArticleDistributionOverviewView,
    ArticleDistributionPendingUserOut,
    ArticleDistributionPublicDashboardOut,
    ArticleDistributionReportOut,
    PublishStatus,
    PublicationType,
)
from .shared import router


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
    if (
        view == "topics"
        and SCOPE_ARTICLE_DISTRIBUTION_METADATA_DASHBOARD_READ
        not in current_user.effective_scopes
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="缺少 article_distribution:metadata_dashboard:read 权限",
        )

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
    "/reports/metadata-dashboard",
    response_model=ArticleDistributionMetadataDashboardOut,
    summary="查看文章元数据选题看板",
)
async def list_metadata_dashboard(
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    account_status: AccountStatusFilter = Query(default="active"),
    publish_status: PublishStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Security(
        get_current_user,
        scopes=[SCOPE_ARTICLE_DISTRIBUTION_METADATA_DASHBOARD_READ],
    ),
):
    def _list():
        return service.list_metadata_dashboard(
            db,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
            publish_status=publish_status,
            page=page,
            page_size=page_size,
        )

    return await run_in_thread(_list)


@router.get(
    "/reports/unpublished",
    response_model=ArticleDistributionReportOut,
    summary="查看全量未发布文章进度",
)
async def list_unpublished_report(
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    account_status: AccountStatusFilter = Query(default="active"),
    db: Session = Depends(get_db),
    _: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ]
    ),
):
    def _list():
        return service.list_unpublished_report(
            db,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
        )

    return await run_in_thread(_list)


@router.get(
    "/reports/unpublished/users/{user_id}",
    response_model=ArticleDistributionPendingUserOut,
    summary="查看单个用户的文章分发明细",
)
async def get_unpublished_report_user_detail(
    user_id: int,
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    account_status: AccountStatusFilter = Query(default="active"),
    db: Session = Depends(get_db),
    _: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ]
    ),
):
    def _get():
        return service.get_unpublished_report_user_detail(
            db,
            user_id=user_id,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
        )

    return await run_in_thread(_get)


@router.get(
    "/reports/missing-traffic/users",
    response_model=ArticleDistributionMissingTrafficReportOut,
    summary="按用户查看未填写新增流量的已发布文章",
)
async def list_missing_traffic_report(
    recorded_from: datetime = Query(...),
    recorded_to: datetime = Query(...),
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    account_status: AccountStatusFilter = Query(default="active"),
    db: Session = Depends(get_db),
    _: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ]
    ),
):
    def _list():
        return service.list_missing_traffic_report(
            db,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
        )

    return await run_in_thread(_list)


@router.get(
    "/reports/missing-traffic/users/{user_id}",
    response_model=ArticleDistributionMissingTrafficUserOut,
    summary="查看单个用户未填写新增流量的文章明细",
)
async def get_missing_traffic_report_user_detail(
    user_id: int,
    recorded_from: datetime = Query(...),
    recorded_to: datetime = Query(...),
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    account_status: AccountStatusFilter = Query(default="active"),
    db: Session = Depends(get_db),
    _: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ]
    ),
):
    def _get():
        return service.get_missing_traffic_report_user_detail(
            db,
            user_id=user_id,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
        )

    return await run_in_thread(_get)


@router.get(
    "/reports/missing-traffic",
    response_model=ArticleDistributionMissingTrafficPageOut,
    summary="查看未填写新增流量的已发布文章",
)
async def list_missing_traffic_articles(
    recorded_from: datetime = Query(...),
    recorded_to: datetime = Query(...),
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    account_status: AccountStatusFilter = Query(default="active"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ]
    ),
):
    def _list():
        return service.list_missing_traffic_articles(
            db,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            platform=platform,
            publication_type=publication_type,
            account_status=account_status,
            page=page,
            page_size=page_size,
        )

    return await run_in_thread(_list)


@router.get(
    "/public/dashboard",
    response_model=ArticleDistributionPublicDashboardOut,
    summary="公开查看已发布文章分发看板",
)
async def list_public_dashboard(
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    def _list():
        return service.list_public_dashboard(
            db,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            publication_type=publication_type,
            page=page,
            page_size=page_size,
        )

    return await run_in_thread(_list)

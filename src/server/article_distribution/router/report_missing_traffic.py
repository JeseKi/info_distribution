# -*- coding: utf-8 -*-
"""Missing traffic report routes for article distribution."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import Depends, Query, Security
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from .. import service
from ..schemas import (
    AccountStatusFilter,
    ArticleDistributionMissingTrafficPageOut,
    ArticleDistributionMissingTrafficReportOut,
    ArticleDistributionMissingTrafficUserOut,
    PublicationType,
)
from .shared import router


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

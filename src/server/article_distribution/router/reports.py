# -*- coding: utf-8 -*-
"""Report routes for article distribution."""

from __future__ import annotations

from datetime import date

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
    ArticleDistributionPendingUserOut,
    ArticleDistributionPublicDashboardOut,
    ArticleDistributionReportOut,
    PublicationType,
)
from .shared import router


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

# -*- coding: utf-8 -*-
"""Overview report routes for article distribution."""

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
    ArticleDistributionOverviewOut,
    ArticleDistributionOverviewView,
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

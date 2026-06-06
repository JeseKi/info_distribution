# -*- coding: utf-8 -*-
"""Metadata dashboard report routes for article distribution."""

from __future__ import annotations

from datetime import date

from fastapi import Depends, Query, Security
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import (
    SCOPE_ARTICLE_DISTRIBUTION_METADATA_DASHBOARD_READ,
)
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from .. import service
from ..schemas import (
    AccountStatusFilter,
    ArticleDistributionMetadataDashboardOut,
    PublishStatus,
    PublicationType,
)
from .shared import router


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

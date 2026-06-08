# -*- coding: utf-8 -*-
"""Public dashboard report routes for article distribution."""

from __future__ import annotations

from datetime import date

from fastapi import Depends, Path, Query
from sqlalchemy.orm import Session

from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from .. import service
from ..schemas import ArticleDistributionPublicDashboardOut, PublicationType
from .shared import router


@router.get(
    "/public/dashboard/{project_code}",
    response_model=ArticleDistributionPublicDashboardOut,
    summary="公开查看已发布文章分发看板",
)
async def list_public_dashboard(
    project_code: str = Path(..., min_length=8, max_length=8),
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
            project_code=project_code,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            publication_type=publication_type,
            page=page,
            page_size=page_size,
        )

    return await run_in_thread(_list)

# -*- coding: utf-8 -*-
"""Project and theme management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Security, status
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_admin, get_current_admin_writer
from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.schemas import UserRole
from src.server.auth.service.scopes import (
    SCOPE_ARTICLE_DISTRIBUTION_READ,
)
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from . import service
from .schemas import (
    AccountOptionsOut,
    ProjectCreate,
    ProjectLookupOut,
    ProjectOut,
    ProjectSummary,
    ProjectUpdate,
    ThemeCreate,
    ThemeOut,
    ThemeUpdate,
    UserProjectsUpdate,
)

admin_router = APIRouter(prefix="/api/admin", tags=["项目主题管理"])
auth_router = APIRouter(prefix="/api/auth", tags=["认证"])
article_router = APIRouter(prefix="/api/article-distribution", tags=["文章分发"])


@admin_router.get("/projects", response_model=list[ProjectOut], summary="列出项目")
async def list_projects(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return await run_in_thread(lambda: service.list_projects(db))


@admin_router.post(
    "/projects",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
)
async def create_project(
    payload: ProjectCreate,
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    return await run_in_thread(lambda: service.create_project(db, payload))


@admin_router.patch("/projects/{project_id}", response_model=ProjectOut, summary="更新项目")
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    return await run_in_thread(lambda: service.update_project(db, project_id, payload))


@admin_router.get("/themes", response_model=list[ThemeOut], summary="列出主题")
async def list_themes(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return await run_in_thread(lambda: service.list_themes(db))


@admin_router.post(
    "/themes",
    response_model=ThemeOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建主题",
)
async def create_theme(
    payload: ThemeCreate,
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    return await run_in_thread(lambda: service.create_theme(db, payload))


@admin_router.patch("/themes/{theme_id}", response_model=ThemeOut, summary="更新主题")
async def update_theme(
    theme_id: int,
    payload: ThemeUpdate,
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    return await run_in_thread(lambda: service.update_theme(db, theme_id, payload))


@admin_router.put(
    "/users/{user_id}/projects",
    response_model=list[ProjectSummary],
    summary="更新用户项目",
)
async def update_user_projects(
    user_id: int,
    payload: UserProjectsUpdate,
    _: User = Depends(get_current_admin_writer),
    db: Session = Depends(get_db),
):
    return await run_in_thread(lambda: service.set_user_projects(db, user_id, payload.project_ids))


@auth_router.get(
    "/projects/lookup",
    response_model=ProjectLookupOut,
    summary="根据项目码查询项目",
)
async def lookup_project(
    code: str = Query(..., min_length=8, max_length=8),
    db: Session = Depends(get_db),
):
    return await run_in_thread(lambda: service.lookup_project_by_code(db, code))


@article_router.get(
    "/account-options",
    response_model=AccountOptionsOut,
    summary="获取分发账号项目和主题选项",
)
async def get_account_options(
    user_id: int | None = Query(default=None, ge=1),
    current_user: User = Security(
        get_current_user,
        scopes=[SCOPE_ARTICLE_DISTRIBUTION_READ],
    ),
    db: Session = Depends(get_db),
):
    target_user_id = current_user.id
    if user_id is not None:
        if current_user.role != UserRole.ADMIN:
            target_user_id = current_user.id
        else:
            target_user_id = user_id
    return await run_in_thread(lambda: service.get_account_options(db, target_user_id))


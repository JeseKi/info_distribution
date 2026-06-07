# -*- coding: utf-8 -*-
"""Project and theme management services."""

from __future__ import annotations

import re
import os
import secrets
import string

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.server.auth.dao import UserDAO

from .dao import ProjectManagementDAO
from .models import Project, Theme
from .schemas import (
    AccountOptionsOut,
    ProjectCreate,
    ProjectLookupOut,
    ProjectOut,
    ProjectSummary,
    ProjectUpdate,
    ThemeCreate,
    ThemeOut,
    ThemeSummary,
    ThemeUpdate,
)

PROJECT_CODE_PATTERN = re.compile(r"^[A-Z]{8}$")


def normalize_name(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label}不能为空",
        )
    return normalized


def normalize_project_code(value: str) -> str:
    normalized = value.strip().upper()
    if not PROJECT_CODE_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目码必须是 8 位大写字母",
        )
    return normalized


def generate_project_code(db: Session) -> str:
    dao = ProjectManagementDAO(db)
    for _ in range(100):
        code = "".join(secrets.choice(string.ascii_uppercase) for _ in range(8))
        if dao.get_project_by_code(code) is None:
            return code
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="项目码生成失败",
    )


def serialize_project(db: Session, project: Project) -> ProjectOut:
    dao = ProjectManagementDAO(db)
    theme_ids = dao.list_project_theme_ids(project.id)
    themes_by_id = {theme.id: theme for theme in dao.list_themes()}
    themes = [
        ThemeSummary.model_validate(themes_by_id[theme_id])
        for theme_id in theme_ids
        if theme_id in themes_by_id
    ]
    return ProjectOut.model_validate(
        {**project.__dict__, "theme_ids": theme_ids, "themes": themes}
    )


def serialize_theme(db: Session, theme: Theme) -> ThemeOut:
    project_ids = ProjectManagementDAO(db).list_theme_project_ids(theme.id)
    return ThemeOut.model_validate({**theme.__dict__, "project_ids": project_ids})


def list_projects(db: Session) -> list[ProjectOut]:
    return [serialize_project(db, project) for project in ProjectManagementDAO(db).list_projects()]


def list_themes(db: Session) -> list[ThemeOut]:
    return [serialize_theme(db, theme) for theme in ProjectManagementDAO(db).list_themes()]


def list_active_projects(db: Session) -> list[ProjectSummary]:
    return [
        ProjectSummary.model_validate(project)
        for project in ProjectManagementDAO(db).list_active_projects()
    ]


def list_user_project_summaries(db: Session, user_id: int) -> list[ProjectSummary]:
    return [
        ProjectSummary.model_validate(project)
        for project in ProjectManagementDAO(db).list_user_projects(user_id)
    ]


def list_user_theme_summaries(db: Session, user_id: int) -> list[ThemeSummary]:
    dao = ProjectManagementDAO(db)
    project_ids = dao.list_user_project_ids(user_id)
    if not project_ids:
        return []
    theme_ids: set[int] = set()
    for project_id in project_ids:
        theme_ids.update(dao.list_project_theme_ids(project_id))
    themes_by_id = {theme.id: theme for theme in dao.list_active_themes()}
    return [
        ThemeSummary.model_validate(themes_by_id[theme_id])
        for theme_id in sorted(theme_ids)
        if theme_id in themes_by_id
    ]


def create_project(db: Session, payload: ProjectCreate) -> ProjectOut:
    dao = ProjectManagementDAO(db)
    name = normalize_name(payload.name, "项目名称")
    code = normalize_project_code(payload.code) if payload.code else generate_project_code(db)
    _assert_theme_ids_exist(db, payload.theme_ids)
    project = Project(name=name, code=code, is_active=payload.is_active)
    try:
        project = dao.create_project(project)
        dao.replace_project_themes(project.id, payload.theme_ids)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目名称或项目码已存在",
        )
    return serialize_project(db, project)


def update_project(db: Session, project_id: int, payload: ProjectUpdate) -> ProjectOut:
    dao = ProjectManagementDAO(db)
    project = dao.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    fields = payload.model_dump(exclude_unset=True)
    if "name" in fields and fields["name"] is not None:
        fields["name"] = normalize_name(str(fields["name"]), "项目名称")
    if "code" in fields and fields["code"] is not None:
        fields["code"] = normalize_project_code(str(fields["code"]))
    theme_ids = fields.pop("theme_ids", None)
    if theme_ids is not None:
        _assert_theme_ids_exist(db, theme_ids)
    try:
        if fields:
            project = dao.update_project(project, **fields)
        if theme_ids is not None:
            dao.replace_project_themes(project.id, theme_ids)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目名称或项目码已存在",
        )
    return serialize_project(db, project)


def create_theme(db: Session, payload: ThemeCreate) -> ThemeOut:
    dao = ProjectManagementDAO(db)
    name = normalize_name(payload.name, "主题名称")
    _assert_project_ids_exist(db, payload.project_ids)
    theme = Theme(name=name, is_active=payload.is_active)
    try:
        theme = dao.create_theme(theme)
        dao.replace_theme_projects(theme.id, payload.project_ids)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="主题名称已存在",
        )
    return serialize_theme(db, theme)


def update_theme(db: Session, theme_id: int, payload: ThemeUpdate) -> ThemeOut:
    dao = ProjectManagementDAO(db)
    theme = dao.get_theme(theme_id)
    if theme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="主题不存在")
    fields = payload.model_dump(exclude_unset=True)
    if "name" in fields and fields["name"] is not None:
        fields["name"] = normalize_name(str(fields["name"]), "主题名称")
    project_ids = fields.pop("project_ids", None)
    if project_ids is not None:
        _assert_project_ids_exist(db, project_ids)
    try:
        if fields:
            theme = dao.update_theme(theme, **fields)
        if project_ids is not None:
            dao.replace_theme_projects(theme.id, project_ids)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="主题名称已存在",
        )
    return serialize_theme(db, theme)


def set_user_projects(db: Session, user_id: int, project_ids: list[int]) -> list[ProjectSummary]:
    if UserDAO(db).get_by_id(user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    _assert_project_ids_exist(db, project_ids)
    ProjectManagementDAO(db).replace_user_projects(user_id, project_ids)
    return list_user_project_summaries(db, user_id)


def attach_user_to_project_code(db: Session, user_id: int, code: str) -> None:
    project = lookup_active_project_by_code(db, code)
    ProjectManagementDAO(db).add_user_project(user_id, project.id)


def lookup_active_project_by_code(db: Session, code: str) -> Project:
    normalized_code = normalize_project_code(code)
    project = ProjectManagementDAO(db).get_project_by_code(normalized_code)
    if project is None or not project.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目码无效或项目已停用",
        )
    return project


def lookup_project_by_code(db: Session, code: str) -> ProjectLookupOut:
    return ProjectLookupOut.model_validate(lookup_active_project_by_code(db, code))


def get_account_options(db: Session, user_id: int) -> AccountOptionsOut:
    return AccountOptionsOut(
        projects=list_user_project_summaries(db, user_id),
        themes=list_user_theme_summaries(db, user_id),
    )


def bootstrap_default_project_theme(db: Session) -> Project:
    dao = ProjectManagementDAO(db)
    project = dao.get_project_by_name("AIFC")
    if project is None:
        code = "AIFCAIFC" if os.getenv("APP_ENV") == "test" else generate_project_code(db)
        if dao.get_project_by_code(code) is not None:
            code = generate_project_code(db)
        project = dao.create_project(
            Project(name="AIFC", code=code, is_active=True)
        )
    theme = dao.get_theme_by_name("AI")
    if theme is None:
        theme = dao.create_theme(Theme(name="AI", is_active=True))
    theme_ids = dao.list_project_theme_ids(project.id)
    if theme.id not in theme_ids:
        dao.replace_project_themes(project.id, [*theme_ids, theme.id])
    return project


def validate_user_theme_id(db: Session, user_id: int, theme_id: int) -> int:
    allowed_ids = {theme.id for theme in list_user_theme_summaries(db, user_id)}
    if theme_id not in allowed_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号主题必须来自该用户所在项目关联的主题",
        )
    return theme_id


def validate_user_project_id(db: Session, user_id: int, project_id: int) -> int:
    dao = ProjectManagementDAO(db)
    project = dao.get_project(project_id)
    if project is None or not project.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文章项目不存在或已停用",
        )
    if project_id not in set(dao.list_user_project_ids(user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文章项目必须属于账号归属用户所在项目",
        )
    return project_id


def _assert_project_ids_exist(db: Session, project_ids: list[int]) -> None:
    dao = ProjectManagementDAO(db)
    missing = [project_id for project_id in set(project_ids) if dao.get_project(project_id) is None]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目不存在",
        )


def _assert_theme_ids_exist(db: Session, theme_ids: list[int]) -> None:
    dao = ProjectManagementDAO(db)
    missing = [theme_id for theme_id in set(theme_ids) if dao.get_theme(theme_id) is None]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="主题不存在",
        )

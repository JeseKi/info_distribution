# -*- coding: utf-8 -*-
"""Project and theme schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ThemeSummary(BaseModel):
    id: int
    name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ProjectSummary(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ThemeOut(ThemeSummary):
    created_at: datetime
    updated_at: datetime
    project_ids: list[int] = Field(default_factory=list)


class ProjectOut(ProjectSummary):
    created_at: datetime
    updated_at: datetime
    theme_ids: list[int] = Field(default_factory=list)
    themes: list[ThemeSummary] = Field(default_factory=list)


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    code: str | None = Field(default=None, min_length=8, max_length=8)
    is_active: bool = True
    theme_ids: list[int] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    code: str | None = Field(default=None, min_length=8, max_length=8)
    is_active: bool | None = None
    theme_ids: list[int] | None = None


class ThemeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    is_active: bool = True
    project_ids: list[int] = Field(default_factory=list)


class ThemeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None
    project_ids: list[int] | None = None


class ProjectThemesUpdate(BaseModel):
    theme_ids: list[int] = Field(default_factory=list)


class UserProjectsUpdate(BaseModel):
    project_ids: list[int] = Field(default_factory=list)


class ProjectLookupOut(ProjectSummary):
    pass


class AccountOptionsOut(BaseModel):
    projects: list[ProjectSummary]
    themes: list[ThemeSummary]


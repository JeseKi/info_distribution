# -*- coding: utf-8 -*-
"""Project and theme DAO methods."""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO

from .models import (
    Project,
    ProjectTheme,
    Theme,
    UserProject,
)


class ProjectManagementDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def list_projects(self) -> list[Project]:
        return self.db_session.query(Project).order_by(Project.id.desc()).all()

    def list_active_projects(self) -> list[Project]:
        return (
            self.db_session.query(Project)
            .filter(Project.is_active.is_(True))
            .order_by(Project.name.asc(), Project.id.asc())
            .all()
        )

    def get_project(self, project_id: int) -> Project | None:
        return self.db_session.query(Project).filter(Project.id == project_id).first()

    def get_project_by_code(self, code: str) -> Project | None:
        return self.db_session.query(Project).filter(Project.code == code).first()

    def get_project_by_name(self, name: str) -> Project | None:
        return self.db_session.query(Project).filter(Project.name == name).first()

    def create_project(self, project: Project) -> Project:
        self.db_session.add(project)
        self.db_session.commit()
        self.db_session.refresh(project)
        return project

    def update_project(self, project: Project, **fields: object) -> Project:
        for key, value in fields.items():
            setattr(project, key, value)
        self.db_session.commit()
        self.db_session.refresh(project)
        return project

    def list_themes(self) -> list[Theme]:
        return self.db_session.query(Theme).order_by(Theme.id.desc()).all()

    def list_active_themes(self) -> list[Theme]:
        return (
            self.db_session.query(Theme)
            .filter(Theme.is_active.is_(True))
            .order_by(Theme.name.asc(), Theme.id.asc())
            .all()
        )

    def get_theme(self, theme_id: int) -> Theme | None:
        return self.db_session.query(Theme).filter(Theme.id == theme_id).first()

    def get_theme_by_name(self, name: str) -> Theme | None:
        return self.db_session.query(Theme).filter(Theme.name == name).first()

    def create_theme(self, theme: Theme) -> Theme:
        self.db_session.add(theme)
        self.db_session.commit()
        self.db_session.refresh(theme)
        return theme

    def update_theme(self, theme: Theme, **fields: object) -> Theme:
        for key, value in fields.items():
            setattr(theme, key, value)
        self.db_session.commit()
        self.db_session.refresh(theme)
        return theme

    def list_project_theme_rows(self) -> list[ProjectTheme]:
        return self.db_session.query(ProjectTheme).all()

    def list_project_theme_ids(self, project_id: int) -> list[int]:
        return [
            row.theme_id
            for row in self.db_session.query(ProjectTheme)
            .filter(ProjectTheme.project_id == project_id)
            .order_by(ProjectTheme.theme_id.asc())
            .all()
        ]

    def list_theme_project_ids(self, theme_id: int) -> list[int]:
        return [
            row.project_id
            for row in self.db_session.query(ProjectTheme)
            .filter(ProjectTheme.theme_id == theme_id)
            .order_by(ProjectTheme.project_id.asc())
            .all()
        ]

    def replace_project_themes(
        self, project_id: int, theme_ids: list[int]
    ) -> list[ProjectTheme]:
        self.db_session.query(ProjectTheme).filter(
            ProjectTheme.project_id == project_id
        ).delete(synchronize_session=False)
        rows = [
            ProjectTheme(project_id=project_id, theme_id=theme_id)
            for theme_id in sorted(set(theme_ids))
        ]
        self.db_session.add_all(rows)
        self.db_session.commit()
        return rows

    def replace_theme_projects(
        self, theme_id: int, project_ids: list[int]
    ) -> list[ProjectTheme]:
        self.db_session.query(ProjectTheme).filter(
            ProjectTheme.theme_id == theme_id
        ).delete(synchronize_session=False)
        rows = [
            ProjectTheme(project_id=project_id, theme_id=theme_id)
            for project_id in sorted(set(project_ids))
        ]
        self.db_session.add_all(rows)
        self.db_session.commit()
        return rows

    def list_user_project_ids(self, user_id: int) -> list[int]:
        return [
            row.project_id
            for row in self.db_session.query(UserProject)
            .filter(UserProject.user_id == user_id)
            .order_by(UserProject.project_id.asc())
            .all()
        ]

    def list_user_projects(self, user_id: int) -> list[Project]:
        return (
            self.db_session.query(Project)
            .join(UserProject, UserProject.project_id == Project.id)
            .filter(UserProject.user_id == user_id)
            .order_by(Project.name.asc(), Project.id.asc())
            .all()
        )

    def replace_user_projects(self, user_id: int, project_ids: list[int]) -> None:
        self.db_session.query(UserProject).filter(UserProject.user_id == user_id).delete(
            synchronize_session=False
        )
        self.db_session.add_all(
            [
                UserProject(user_id=user_id, project_id=project_id)
                for project_id in sorted(set(project_ids))
            ]
        )
        self.db_session.commit()

    def add_user_project(self, user_id: int, project_id: int) -> UserProject:
        existing = (
            self.db_session.query(UserProject)
            .filter(UserProject.user_id == user_id, UserProject.project_id == project_id)
            .first()
        )
        if existing:
            return existing
        row = UserProject(user_id=user_id, project_id=project_id)
        self.db_session.add(row)
        self.db_session.commit()
        self.db_session.refresh(row)
        return row

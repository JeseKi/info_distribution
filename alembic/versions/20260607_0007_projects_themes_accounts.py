"""add projects and themes

Revision ID: 20260607_0007
Revises: 20260606_0006
Create Date: 2026-06-07
"""

from __future__ import annotations

from datetime import datetime, timezone
import secrets
import string

from alembic import op
import sqlalchemy as sa


revision = "20260607_0007"
down_revision = "20260606_0006"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    columns = sa.inspect(op.get_bind()).get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def _generate_project_code() -> str:
    bind = op.get_bind()
    for _ in range(100):
        code = "".join(secrets.choice(string.ascii_uppercase) for _ in range(8))
        existing = bind.execute(
            sa.text("select id from projects where code = :code"),
            {"code": code},
        ).first()
        if existing is None:
            return code
    raise RuntimeError("failed to generate project code")


def _ensure_seed_rows() -> tuple[int, int]:
    bind = op.get_bind()
    now = datetime.now(timezone.utc)

    project_row = bind.execute(
        sa.text("select id from projects where name = :name"),
        {"name": "AIFC"},
    ).first()
    if project_row is None:
        bind.execute(
            sa.text(
                """
                insert into projects (name, code, is_active, created_at, updated_at)
                values (:name, :code, :is_active, :created_at, :updated_at)
                """
            ),
            {
                "name": "AIFC",
                "code": _generate_project_code(),
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        )
        project_row = bind.execute(
            sa.text("select id from projects where name = :name"),
            {"name": "AIFC"},
        ).first()
    if project_row is None:
        raise RuntimeError("failed to seed AIFC project")

    theme_row = bind.execute(
        sa.text("select id from themes where name = :name"),
        {"name": "AI"},
    ).first()
    if theme_row is None:
        bind.execute(
            sa.text(
                """
                insert into themes (name, is_active, created_at, updated_at)
                values (:name, :is_active, :created_at, :updated_at)
                """
            ),
            {
                "name": "AI",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        )
        theme_row = bind.execute(
            sa.text("select id from themes where name = :name"),
            {"name": "AI"},
        ).first()
    if theme_row is None:
        raise RuntimeError("failed to seed AI theme")

    project_id = int(project_row[0])
    theme_id = int(theme_row[0])
    existing_link = bind.execute(
        sa.text(
            """
            select id from project_themes
            where project_id = :project_id and theme_id = :theme_id
            """
        ),
        {"project_id": project_id, "theme_id": theme_id},
    ).first()
    if existing_link is None:
        bind.execute(
            sa.text(
                """
                insert into project_themes (project_id, theme_id)
                values (:project_id, :theme_id)
                """
            ),
            {"project_id": project_id, "theme_id": theme_id},
        )
    return project_id, theme_id


def _backfill_existing_rows(project_id: int, theme_id: int) -> None:
    bind = op.get_bind()

    if _table_exists("users"):
        user_rows = bind.execute(sa.text("select id from users")).all()
        for row in user_rows:
            user_id = int(row[0])
            existing = bind.execute(
                sa.text(
                    """
                    select id from user_projects
                    where user_id = :user_id and project_id = :project_id
                    """
                ),
                {"user_id": user_id, "project_id": project_id},
            ).first()
            if existing is None:
                bind.execute(
                    sa.text(
                        """
                        insert into user_projects (user_id, project_id)
                        values (:user_id, :project_id)
                        """
                    ),
                    {"user_id": user_id, "project_id": project_id},
                )

    if _table_exists("article_distribution_accounts") and _column_exists(
        "article_distribution_accounts", "theme_id"
    ):
        bind.execute(
            sa.text(
                """
                update article_distribution_accounts
                set theme_id = :theme_id
                where theme_id is null
                """
            ),
            {"theme_id": theme_id},
        )


def upgrade() -> None:
    if not _table_exists("projects"):
        op.create_table(
            "projects",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("code", sa.String(length=8), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("name", name="uq_projects_name"),
            sa.UniqueConstraint("code", name="uq_projects_code"),
        )
        op.create_index("ix_projects_code", "projects", ["code"])

    if not _table_exists("themes"):
        op.create_table(
            "themes",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("name", name="uq_themes_name"),
        )

    if not _table_exists("project_themes"):
        op.create_table(
            "project_themes",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("theme_id", sa.Integer(), nullable=False),
            sa.UniqueConstraint("project_id", "theme_id", name="uq_project_theme"),
        )
        op.create_index("ix_project_themes_project_id", "project_themes", ["project_id"])
        op.create_index("ix_project_themes_theme_id", "project_themes", ["theme_id"])

    if not _table_exists("user_projects"):
        op.create_table(
            "user_projects",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.UniqueConstraint("user_id", "project_id", name="uq_user_project"),
        )
        op.create_index("ix_user_projects_user_id", "user_projects", ["user_id"])
        op.create_index("ix_user_projects_project_id", "user_projects", ["project_id"])

    if _table_exists("article_distribution_accounts") and not _column_exists(
        "article_distribution_accounts", "theme_id"
    ):
        op.add_column(
            "article_distribution_accounts",
            sa.Column("theme_id", sa.Integer(), nullable=True),
        )
        op.create_index(
            "ix_article_distribution_accounts_theme_id",
            "article_distribution_accounts",
            ["theme_id"],
        )

    project_id, theme_id = _ensure_seed_rows()
    _backfill_existing_rows(project_id, theme_id)


def downgrade() -> None:
    if _column_exists("article_distribution_accounts", "theme_id"):
        try:
            op.drop_index(
                "ix_article_distribution_accounts_theme_id",
                table_name="article_distribution_accounts",
            )
        except Exception:
            pass
        op.drop_column("article_distribution_accounts", "theme_id")

    for table_name in (
        "user_projects",
        "project_themes",
        "themes",
        "projects",
    ):
        if _table_exists(table_name):
            op.drop_table(table_name)

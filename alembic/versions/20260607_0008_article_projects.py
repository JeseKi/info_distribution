"""add project relation to articles

Revision ID: 20260607_0008
Revises: 20260607_0007
Create Date: 2026-06-07
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260607_0008"
down_revision = "20260607_0007"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    columns = sa.inspect(op.get_bind()).get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def _index_exists(table_name: str, index_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def _get_aifc_project_id() -> int:
    project_row = op.get_bind().execute(
        sa.text("select id from projects where name = :name"),
        {"name": "AIFC"},
    ).first()
    if project_row is None:
        raise RuntimeError("AIFC project must exist before article project migration")
    return int(project_row[0])


def upgrade() -> None:
    if not _table_exists("article_distribution_articles"):
        return

    if not _column_exists("article_distribution_articles", "project_id"):
        op.add_column(
            "article_distribution_articles",
            sa.Column("project_id", sa.Integer(), nullable=True),
        )
        op.create_index(
            "ix_article_distribution_articles_project_id",
            "article_distribution_articles",
            ["project_id"],
        )
    elif not _index_exists(
        "article_distribution_articles",
        "ix_article_distribution_articles_project_id",
    ):
        op.create_index(
            "ix_article_distribution_articles_project_id",
            "article_distribution_articles",
            ["project_id"],
        )

    project_id = _get_aifc_project_id()
    op.get_bind().execute(
        sa.text(
            """
            update article_distribution_articles
            set project_id = :project_id
            where project_id is null
            """
        ),
        {"project_id": project_id},
    )

    with op.batch_alter_table("article_distribution_articles") as batch_op:
        batch_op.alter_column("project_id", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    if not _column_exists("article_distribution_articles", "project_id"):
        return

    try:
        op.drop_index(
            "ix_article_distribution_articles_project_id",
            table_name="article_distribution_articles",
        )
    except Exception:
        pass
    op.drop_column("article_distribution_articles", "project_id")

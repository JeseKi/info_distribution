"""add article distribution published url

Revision ID: 20260519_0002
Revises: 20260519_0001
Create Date: 2026-05-19
"""

from alembic import op
import sqlalchemy as sa


revision = "20260519_0002"
down_revision = "20260519_0001"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    columns = sa.inspect(op.get_bind()).get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def upgrade() -> None:
    if not _column_exists("article_distribution_articles", "published_url"):
        op.add_column(
            "article_distribution_articles",
            sa.Column("published_url", sa.String(length=2048), nullable=True),
        )


def downgrade() -> None:
    if _column_exists("article_distribution_articles", "published_url"):
        op.drop_column("article_distribution_articles", "published_url")

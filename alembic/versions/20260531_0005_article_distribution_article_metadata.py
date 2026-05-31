"""add article distribution article metadata

Revision ID: 20260531_0005
Revises: 20260524_0004
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa


revision = "20260531_0005"
down_revision = "20260524_0004"
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
    if not _column_exists("article_distribution_articles", "metadata"):
        op.add_column(
            "article_distribution_articles",
            sa.Column("metadata", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    if _column_exists("article_distribution_articles", "metadata"):
        op.drop_column("article_distribution_articles", "metadata")

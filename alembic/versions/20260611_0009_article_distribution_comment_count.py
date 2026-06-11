"""add article distribution comment count

Revision ID: 20260611_0009
Revises: 20260607_0008
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa


revision = "20260611_0009"
down_revision = "20260607_0008"
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
    if not _column_exists(
        "article_distribution_traffic_stats", "comment_count"
    ):
        op.add_column(
            "article_distribution_traffic_stats",
            sa.Column(
                "comment_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )


def downgrade() -> None:
    if _column_exists("article_distribution_traffic_stats", "comment_count"):
        op.drop_column(
            "article_distribution_traffic_stats", "comment_count"
        )

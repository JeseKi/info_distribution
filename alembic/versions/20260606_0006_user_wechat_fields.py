"""add wechat fields to users

Revision ID: 20260606_0006
Revises: 20260531_0005
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260606_0006"
down_revision = "20260531_0005"
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
    if not _column_exists("users", "wechat_nickname"):
        op.add_column(
            "users", sa.Column("wechat_nickname", sa.String(length=100), nullable=True)
        )
    if not _column_exists("users", "wechat_id"):
        op.add_column(
            "users", sa.Column("wechat_id", sa.String(length=100), nullable=True)
        )


def downgrade() -> None:
    if _column_exists("users", "wechat_id"):
        op.drop_column("users", "wechat_id")
    if _column_exists("users", "wechat_nickname"):
        op.drop_column("users", "wechat_nickname")

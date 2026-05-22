"""add article distribution account active flag

Revision ID: 20260522_0003
Revises: 20260519_0002
Create Date: 2026-05-22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260522_0003"
down_revision = "20260519_0002"
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


def upgrade() -> None:
    if not _column_exists("article_distribution_accounts", "is_active"):
        op.add_column(
            "article_distribution_accounts",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if not _index_exists(
        "article_distribution_accounts", "ix_article_distribution_accounts_is_active"
    ):
        op.create_index(
            op.f("ix_article_distribution_accounts_is_active"),
            "article_distribution_accounts",
            ["is_active"],
            unique=False,
        )


def downgrade() -> None:
    if _index_exists(
        "article_distribution_accounts", "ix_article_distribution_accounts_is_active"
    ):
        op.drop_index(
            op.f("ix_article_distribution_accounts_is_active"),
            table_name="article_distribution_accounts",
        )
    if _column_exists("article_distribution_accounts", "is_active"):
        op.drop_column("article_distribution_accounts", "is_active")

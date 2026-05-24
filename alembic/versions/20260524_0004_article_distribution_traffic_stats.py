"""add article distribution traffic stats

Revision ID: 20260524_0004
Revises: 20260522_0003
Create Date: 2026-05-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260524_0004"
down_revision = "20260522_0003"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _index_exists(table_name: str, index_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def _create_index_once(table_name: str, index_name: str, columns: list[str]) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(op.f(index_name), table_name, columns, unique=False)


def _drop_index_if_exists(table_name: str, index_name: str) -> None:
    if _index_exists(table_name, index_name):
        op.drop_index(op.f(index_name), table_name=table_name)


def upgrade() -> None:
    if not _table_exists("article_distribution_traffic_stats"):
        op.create_table(
            "article_distribution_traffic_stats",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("account_id", sa.Integer(), nullable=False),
            sa.Column("article_id", sa.Integer(), nullable=False),
            sa.Column("read_count", sa.Integer(), nullable=False),
            sa.Column("like_count", sa.Integer(), nullable=False),
            sa.Column("favorite_count", sa.Integer(), nullable=False),
            sa.Column("share_count", sa.Integer(), nullable=False),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_once(
        "article_distribution_traffic_stats",
        "ix_article_distribution_traffic_stats_user_id",
        ["user_id"],
    )
    _create_index_once(
        "article_distribution_traffic_stats",
        "ix_article_distribution_traffic_stats_account_id",
        ["account_id"],
    )
    _create_index_once(
        "article_distribution_traffic_stats",
        "ix_article_distribution_traffic_stats_article_id",
        ["article_id"],
    )
    _create_index_once(
        "article_distribution_traffic_stats",
        "ix_article_distribution_traffic_stats_recorded_at",
        ["recorded_at"],
    )
    _create_index_once(
        "article_distribution_traffic_stats",
        "ix_article_distribution_traffic_stats_article_recorded",
        ["article_id", "recorded_at"],
    )


def downgrade() -> None:
    _drop_index_if_exists(
        "article_distribution_traffic_stats",
        "ix_article_distribution_traffic_stats_article_recorded",
    )
    _drop_index_if_exists(
        "article_distribution_traffic_stats",
        "ix_article_distribution_traffic_stats_recorded_at",
    )
    _drop_index_if_exists(
        "article_distribution_traffic_stats",
        "ix_article_distribution_traffic_stats_article_id",
    )
    _drop_index_if_exists(
        "article_distribution_traffic_stats",
        "ix_article_distribution_traffic_stats_account_id",
    )
    _drop_index_if_exists(
        "article_distribution_traffic_stats",
        "ix_article_distribution_traffic_stats_user_id",
    )
    if _table_exists("article_distribution_traffic_stats"):
        op.drop_table("article_distribution_traffic_stats")

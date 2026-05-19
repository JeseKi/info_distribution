"""create article distribution tables

Revision ID: 20260519_0001
Revises:
Create Date: 2026-05-19
"""

from alembic import op
import sqlalchemy as sa


revision = "20260519_0001"
down_revision = None
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


def _drop_table_if_exists(table_name: str) -> None:
    if _table_exists(table_name):
        op.drop_table(table_name)


def upgrade() -> None:
    if not _table_exists("article_distribution_accounts"):
        op.create_table(
            "article_distribution_accounts",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("account_name", sa.String(length=120), nullable=False),
            sa.Column("platform", sa.String(length=80), nullable=False),
            sa.Column("publication_type", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id",
                "account_name",
                "platform",
                "publication_type",
                name="uq_article_distribution_account_identity",
            ),
        )
    _create_index_once(
        "article_distribution_accounts",
        "ix_article_distribution_accounts_user_id",
        ["user_id"],
    )
    _create_index_once(
        "article_distribution_accounts",
        "ix_article_distribution_accounts_platform",
        ["platform"],
    )
    _create_index_once(
        "article_distribution_accounts",
        "ix_article_distribution_accounts_publication_type",
        ["publication_type"],
    )

    if not _table_exists("article_distribution_articles"):
        op.create_table(
            "article_distribution_articles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("account_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("markdown_content", sa.Text(), nullable=False),
            sa.Column("scheduled_date", sa.Date(), nullable=False),
            sa.Column("publish_status", sa.String(length=20), nullable=False),
            sa.Column("source", sa.String(length=40), nullable=False),
            sa.Column("created_by_user_id", sa.Integer(), nullable=True),
            sa.Column("api_key_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_once(
        "article_distribution_articles",
        "ix_article_distribution_articles_user_id",
        ["user_id"],
    )
    _create_index_once(
        "article_distribution_articles",
        "ix_article_distribution_articles_account_id",
        ["account_id"],
    )
    _create_index_once(
        "article_distribution_articles",
        "ix_article_distribution_articles_scheduled_date",
        ["scheduled_date"],
    )
    _create_index_once(
        "article_distribution_articles",
        "ix_article_distribution_articles_publish_status",
        ["publish_status"],
    )

    if not _table_exists("article_distribution_api_keys"):
        op.create_table(
            "article_distribution_api_keys",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("key_prefix", sa.String(length=24), nullable=False),
            sa.Column("key_hash", sa.String(length=64), nullable=False),
            sa.Column("created_by_user_id", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("key_hash"),
        )
    _create_index_once(
        "article_distribution_api_keys",
        "ix_article_distribution_api_keys_key_prefix",
        ["key_prefix"],
    )
    _create_index_once(
        "article_distribution_api_keys",
        "ix_article_distribution_api_keys_created_by_user_id",
        ["created_by_user_id"],
    )


def downgrade() -> None:
    _drop_index_if_exists(
        "article_distribution_api_keys",
        "ix_article_distribution_api_keys_created_by_user_id",
    )
    _drop_index_if_exists(
        "article_distribution_api_keys",
        "ix_article_distribution_api_keys_key_prefix",
    )
    _drop_table_if_exists("article_distribution_api_keys")
    _drop_index_if_exists(
        "article_distribution_articles",
        "ix_article_distribution_articles_publish_status",
    )
    _drop_index_if_exists(
        "article_distribution_articles",
        "ix_article_distribution_articles_scheduled_date",
    )
    _drop_index_if_exists(
        "article_distribution_articles",
        "ix_article_distribution_articles_account_id",
    )
    _drop_index_if_exists(
        "article_distribution_articles",
        "ix_article_distribution_articles_user_id",
    )
    _drop_table_if_exists("article_distribution_articles")
    _drop_index_if_exists(
        "article_distribution_accounts",
        "ix_article_distribution_accounts_publication_type",
    )
    _drop_index_if_exists(
        "article_distribution_accounts",
        "ix_article_distribution_accounts_platform",
    )
    _drop_index_if_exists(
        "article_distribution_accounts",
        "ix_article_distribution_accounts_user_id",
    )
    _drop_table_if_exists("article_distribution_accounts")

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


def upgrade() -> None:
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
    op.create_index(
        op.f("ix_article_distribution_accounts_user_id"),
        "article_distribution_accounts",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_article_distribution_accounts_platform"),
        "article_distribution_accounts",
        ["platform"],
        unique=False,
    )
    op.create_index(
        op.f("ix_article_distribution_accounts_publication_type"),
        "article_distribution_accounts",
        ["publication_type"],
        unique=False,
    )

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
    op.create_index(
        op.f("ix_article_distribution_articles_user_id"),
        "article_distribution_articles",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_article_distribution_articles_account_id"),
        "article_distribution_articles",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_article_distribution_articles_scheduled_date"),
        "article_distribution_articles",
        ["scheduled_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_article_distribution_articles_publish_status"),
        "article_distribution_articles",
        ["publish_status"],
        unique=False,
    )

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
    op.create_index(
        op.f("ix_article_distribution_api_keys_key_prefix"),
        "article_distribution_api_keys",
        ["key_prefix"],
        unique=False,
    )
    op.create_index(
        op.f("ix_article_distribution_api_keys_created_by_user_id"),
        "article_distribution_api_keys",
        ["created_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_article_distribution_api_keys_created_by_user_id"),
        table_name="article_distribution_api_keys",
    )
    op.drop_index(
        op.f("ix_article_distribution_api_keys_key_prefix"),
        table_name="article_distribution_api_keys",
    )
    op.drop_table("article_distribution_api_keys")
    op.drop_index(
        op.f("ix_article_distribution_articles_publish_status"),
        table_name="article_distribution_articles",
    )
    op.drop_index(
        op.f("ix_article_distribution_articles_scheduled_date"),
        table_name="article_distribution_articles",
    )
    op.drop_index(
        op.f("ix_article_distribution_articles_account_id"),
        table_name="article_distribution_articles",
    )
    op.drop_index(
        op.f("ix_article_distribution_articles_user_id"),
        table_name="article_distribution_articles",
    )
    op.drop_table("article_distribution_articles")
    op.drop_index(
        op.f("ix_article_distribution_accounts_publication_type"),
        table_name="article_distribution_accounts",
    )
    op.drop_index(
        op.f("ix_article_distribution_accounts_platform"),
        table_name="article_distribution_accounts",
    )
    op.drop_index(
        op.f("ix_article_distribution_accounts_user_id"),
        table_name="article_distribution_accounts",
    )
    op.drop_table("article_distribution_accounts")

"""Add users and user_tracked_events tables

Revision ID: 003_add_user_and_tracking
Revises: 002_add_previous_probability
Create Date: 2026-03-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003_add_user_and_tracking"
down_revision: Union[str, None] = "002_add_previous_probability"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("clerk_id", sa.String(200), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
    )

    op.create_table(
        "user_tracked_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            UUID(as_uuid=True),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "event_id"),
    )

    # Make ticker nullable on companies (users can create companies without tickers)
    op.alter_column("companies", "ticker", existing_type=sa.String(10), nullable=True)


def downgrade() -> None:
    op.alter_column("companies", "ticker", existing_type=sa.String(10), nullable=False)
    op.drop_table("user_tracked_events")
    op.drop_table("users")

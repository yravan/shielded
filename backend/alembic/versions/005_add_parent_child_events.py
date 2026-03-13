"""Add parent/child event hierarchy and market_ticker

Revision ID: 005_add_parent_child_events
Revises: 004_multi_company
Create Date: 2026-03-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "005_add_parent_child_events"
down_revision: Union[str, None] = "004_multi_company"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("parent_event_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_events_parent_event_id",
        "events",
        "events",
        ["parent_event_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_events_parent_event_id", "events", ["parent_event_id"])

    op.add_column(
        "events",
        sa.Column("is_parent", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    op.add_column(
        "events",
        sa.Column("market_ticker", sa.String(200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("events", "market_ticker")
    op.drop_column("events", "is_parent")
    op.drop_index("ix_events_parent_event_id", table_name="events")
    op.drop_constraint("fk_events_parent_event_id", "events", type_="foreignkey")
    op.drop_column("events", "parent_event_id")

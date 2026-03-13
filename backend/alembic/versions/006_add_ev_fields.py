"""Add expected_value and is_quantitative columns to events

Revision ID: 006_add_ev_fields
Revises: 005_add_parent_child_events
Create Date: 2026-03-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_add_ev_fields"
down_revision: Union[str, None] = "005_add_parent_child_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column(
            "is_quantitative",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "events",
        sa.Column("expected_value", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("events", "expected_value")
    op.drop_column("events", "is_quantitative")

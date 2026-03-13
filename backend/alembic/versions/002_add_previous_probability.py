"""Add previous_probability column to events

Revision ID: 002_add_previous_probability
Revises: 001_initial
Create Date: 2026-03-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_add_previous_probability"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("events", sa.Column("previous_probability", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "previous_probability")

"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2026-03-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Events table
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("region", sa.String(100), nullable=False, server_default="Global"),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(200), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=False, server_default=""),
        sa.Column("current_probability", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("resolution_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("source", "source_id", name="uq_event_source_source_id"),
    )

    # Probability history table
    # In production with TimescaleDB:
    #   SELECT create_hypertable('probability_history', 'recorded_at');
    op.create_table(
        "probability_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("source_bid", sa.Float(), nullable=True),
        sa.Column("source_ask", sa.Float(), nullable=True),
        sa.Column("volume_24h", sa.Float(), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
    )

    # Companies table
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("ticker", sa.String(10), nullable=False, unique=True),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("annual_revenue", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("operating_expense", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("capital_expense", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Exposures table
    op.create_table(
        "exposures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("exposure_type", sa.String(50), nullable=False),
        sa.Column("exposure_direction", sa.String(20), nullable=False),
        sa.Column("sensitivity", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("revenue_impact_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("opex_impact_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("capex_impact_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "company_id", "event_id", "exposure_type", name="uq_exposure_company_event_type"
        ),
    )

    # Hedge analyses table
    op.create_table(
        "hedge_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("pm_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("pm_payout", sa.Float(), nullable=False, server_default="0"),
        sa.Column("pm_roi", sa.Float(), nullable=False, server_default="0"),
        sa.Column("traditional_instrument", sa.String(200), nullable=False, server_default=""),
        sa.Column("traditional_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("traditional_payout", sa.Float(), nullable=False, server_default="0"),
        sa.Column("traditional_roi", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recommendation", sa.String(50), nullable=False, server_default="blend"),
        sa.Column("savings_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("hedge_analyses")
    op.drop_table("exposures")
    op.drop_table("companies")
    op.drop_table("probability_history")
    op.drop_table("events")

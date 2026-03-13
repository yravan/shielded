"""Add ingestion fields: image_url, tags, series_ticker, volume, clob_token_id

Revision ID: 008_ingestion_fields
Revises: 007_risk_profile_exposure
Create Date: 2026-03-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "008_ingestion_fields"
down_revision = "007_risk_profile_exposure"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("image_url", sa.Text(), nullable=True))
    op.add_column(
        "events",
        sa.Column("tags", ARRAY(sa.String()), nullable=True, server_default="{}"),
    )
    op.add_column("events", sa.Column("series_ticker", sa.String(100), nullable=True))
    op.add_column("events", sa.Column("volume", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "volume")
    op.drop_column("events", "series_ticker")
    op.drop_column("events", "tags")
    op.drop_column("events", "image_url")

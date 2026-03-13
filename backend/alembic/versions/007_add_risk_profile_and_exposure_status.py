"""Add risk_profile and risk_score to companies, status/relevance to exposures

Revision ID: 007_risk_profile_exposure
Revises: 006_add_ev_fields
Create Date: 2026-03-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = "007_risk_profile_exposure"
down_revision = "006_add_ev_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Company: risk profile and cached risk score
    op.add_column("companies", sa.Column("risk_profile", JSON, server_default="{}", nullable=False))
    op.add_column("companies", sa.Column("risk_score", sa.Integer(), nullable=True))

    # Exposure: status for suggested/confirmed/dismissed workflow
    op.add_column("exposures", sa.Column("status", sa.String(20), server_default="confirmed", nullable=False))
    op.add_column("exposures", sa.Column("relevance_score", sa.Integer(), nullable=True))
    op.add_column("exposures", sa.Column("matched_themes", JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("exposures", "matched_themes")
    op.drop_column("exposures", "relevance_score")
    op.drop_column("exposures", "status")
    op.drop_column("companies", "risk_score")
    op.drop_column("companies", "risk_profile")

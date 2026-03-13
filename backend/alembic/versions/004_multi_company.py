"""Multi-company support: move FK from users.company_id to companies.user_id

Revision ID: 004_multi_company
Revises: 003_add_user_and_tracking
Create Date: 2026-03-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "004_multi_company"
down_revision: Union[str, None] = "003_add_user_and_tracking"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id to companies
    op.add_column("companies", sa.Column("user_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_companies_user_id", "companies", "users", ["user_id"], ["id"])

    # Migrate: for each user with company_id, set that company's user_id
    op.execute(
        """
        UPDATE companies c
        SET user_id = u.id
        FROM users u
        WHERE u.company_id = c.id
        """
    )

    # Drop company_id FK from users
    op.drop_constraint("users_company_id_fkey", "users", type_="foreignkey")
    op.drop_column("users", "company_id")

    # Remove unique constraint on ticker (multiple users may have same company ticker)
    op.drop_constraint("companies_ticker_key", "companies", type_="unique")


def downgrade() -> None:
    # Re-add unique constraint on ticker
    op.create_unique_constraint("companies_ticker_key", "companies", ["ticker"])

    # Re-add company_id to users
    op.add_column("users", sa.Column("company_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("users_company_id_fkey", "users", "companies", ["company_id"], ["id"])

    # Migrate back: take first company per user
    op.execute(
        """
        UPDATE users u
        SET company_id = (
            SELECT c.id FROM companies c WHERE c.user_id = u.id LIMIT 1
        )
        """
    )

    # Drop user_id from companies
    op.drop_constraint("fk_companies_user_id", "companies", type_="foreignkey")
    op.drop_column("companies", "user_id")

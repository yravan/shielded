import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Exposure(Base):
    __tablename__ = "exposures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    exposure_type: Mapped[str] = mapped_column(
        String(50)
    )  # revenue, supply_chain, regulatory, operational
    exposure_direction: Mapped[str] = mapped_column(
        String(20)
    )  # negative, positive, mixed
    sensitivity: Mapped[float] = mapped_column(Float, default=0.5)
    revenue_impact_pct: Mapped[float] = mapped_column(Float, default=0.0)
    opex_impact_pct: Mapped[float] = mapped_column(Float, default=0.0)
    capex_impact_pct: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    company = relationship("Company", back_populates="exposures")
    event = relationship("Event", back_populates="exposures")

    __table_args__ = (
        UniqueConstraint(
            "company_id", "event_id", "exposure_type", name="uq_exposure_company_event_type"
        ),
    )

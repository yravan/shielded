import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class HedgeAnalysis(Base):
    __tablename__ = "hedge_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    pm_cost: Mapped[float] = mapped_column(Float, default=0.0)
    pm_payout: Mapped[float] = mapped_column(Float, default=0.0)
    pm_roi: Mapped[float] = mapped_column(Float, default=0.0)
    traditional_instrument: Mapped[str] = mapped_column(String(200), default="")
    traditional_cost: Mapped[float] = mapped_column(Float, default=0.0)
    traditional_payout: Mapped[float] = mapped_column(Float, default=0.0)
    traditional_roi: Mapped[float] = mapped_column(Float, default=0.0)
    recommendation: Mapped[str] = mapped_column(String(50), default="blend")
    savings_percent: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    company = relationship("Company", back_populates="hedge_analyses")
    event = relationship("Event", back_populates="hedge_analyses")

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(
        String(50)
    )  # geopolitical, trade, regulatory, climate, conflict, economic
    region: Mapped[str] = mapped_column(String(100), default="Global")
    source: Mapped[str] = mapped_column(String(50))  # polymarket, kalshi, metaculus
    source_id: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str] = mapped_column(String(500), default="")
    current_probability: Mapped[float] = mapped_column(Float, default=0.5)
    resolution_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, resolved, expired
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    probability_history = relationship(
        "ProbabilityHistory", back_populates="event", lazy="selectin"
    )
    exposures = relationship("Exposure", back_populates="event", lazy="selectin")
    hedge_analyses = relationship("HedgeAnalysis", back_populates="event", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_event_source_source_id"),
    )

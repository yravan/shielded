import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
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
    previous_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
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
    parent_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    is_parent: Mapped[bool] = mapped_column(Boolean, default=False)
    market_ticker: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_quantitative: Mapped[bool] = mapped_column(Boolean, default=False)
    expected_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True, default=list)
    series_ticker: Mapped[str | None] = mapped_column(String(100), nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)

    parent = relationship(
        "Event", remote_side="Event.id", back_populates="children", lazy="noload"
    )
    children = relationship("Event", back_populates="parent", lazy="noload")
    exposures = relationship("Exposure", back_populates="event", lazy="noload")
    hedge_analyses = relationship("HedgeAnalysis", back_populates="event", lazy="noload")

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_event_source_source_id"),
    )

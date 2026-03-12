from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProbabilityHistory(Base):
    """Stores time-series probability data for events.

    In production, this table would be converted to a TimescaleDB hypertable:
        SELECT create_hypertable('probability_history', 'recorded_at');
    """

    __tablename__ = "probability_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    probability: Mapped[float] = mapped_column(Float)
    source_bid: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_ask: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )

    event = relationship("Event", back_populates="probability_history")

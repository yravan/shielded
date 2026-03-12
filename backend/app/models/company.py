import uuid
from datetime import datetime

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200))
    ticker: Mapped[str] = mapped_column(String(10), unique=True)
    sector: Mapped[str] = mapped_column(String(100))
    annual_revenue: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    operating_expense: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    capital_expense: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    exposures = relationship("Exposure", back_populates="company", lazy="selectin")
    hedge_analyses = relationship("HedgeAnalysis", back_populates="company", lazy="selectin")

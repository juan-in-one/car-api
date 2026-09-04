import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MaintenanceType(str, enum.Enum):
    oil_change = "oil_change"
    itv = "itv"
    timing_belt = "timing_belt"
    other = "other"


class MaintenanceEvent(Base):
    """Un evento de mantenimiento del coche: cambio de aceite, ITV, distribución, etc."""

    __tablename__ = "maintenance_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[MaintenanceType] = mapped_column(
        Enum(MaintenanceType, name="maintenance_type"), nullable=False
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    odometer_km: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

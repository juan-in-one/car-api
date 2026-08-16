import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models import MaintenanceType


class MaintenanceEventBase(BaseModel):
    type: MaintenanceType
    event_date: date
    odometer_km: int
    notes: str | None = None


class MaintenanceEventCreate(MaintenanceEventBase):
    pass


class MaintenanceEventOut(MaintenanceEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime

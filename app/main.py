import uuid

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, init_db
from app.models import MaintenanceEvent
from app.schemas import MaintenanceEventCreate, MaintenanceEventOut

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/maintenance-events", response_model=MaintenanceEventOut, status_code=201)
async def create_event(
    payload: MaintenanceEventCreate, db: AsyncSession = Depends(get_db)
) -> MaintenanceEvent:
    event = MaintenanceEvent(**payload.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@app.get("/maintenance-events", response_model=list[MaintenanceEventOut])
async def list_events(db: AsyncSession = Depends(get_db)) -> list[MaintenanceEvent]:
    result = await db.execute(select(MaintenanceEvent).order_by(MaintenanceEvent.event_date.desc()))
    return list(result.scalars().all())


@app.get("/maintenance-events/{event_id}", response_model=MaintenanceEventOut)
async def get_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> MaintenanceEvent:
    event = await db.get(MaintenanceEvent, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.delete("/maintenance-events/{event_id}", status_code=204)
async def delete_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    event = await db.get(MaintenanceEvent, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(event)
    await db.commit()

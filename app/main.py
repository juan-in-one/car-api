import uuid

from fastapi import Depends, FastAPI, HTTPException
from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from prometheus_client import make_asgi_app
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, init_db
from app.models import MaintenanceEvent
from app.schemas import MaintenanceEventCreate, MaintenanceEventOut

app = FastAPI(title=settings.app_name)

# Métricas de aplicación con OpenTelemetry (mismo SDK que se reutilizará para
# trazas en una fase posterior). El exportador de Prometheus expone las
# métricas en formato texto en /metrics, dentro de esta misma app y puerto —
# Prometheus las scrapea con un ServiceMonitor propio (chart/templates/
# servicemonitor.yaml), sin ningún colector en medio.
metrics.set_meter_provider(
    MeterProvider(
        metric_readers=[PrometheusMetricReader()],
        # Identifica el servicio en las métricas (service_name) — sin esto
        # sale "unknown_service", y hará falta para cruzar datos con logs/
        # trazas en fases posteriores.
        resource=Resource.create({"service.name": "car-api"}),
    )
)
meter = metrics.get_meter("car-api")

# Auto-instrumentación: peticiones/latencia/status de TODAS las rutas, sin
# tocar cada endpoint uno a uno.
FastAPIInstrumentor.instrument_app(app)

# Monta el /metrics que lee el ServiceMonitor.
app.mount("/metrics", make_asgi_app())

# Métrica de negocio propia (no genérica): cuántos eventos de mantenimiento
# se han creado de verdad, incrementada a mano justo donde ocurre el evento
# (ver create_event más abajo) — la auto-instrumentación de arriba no sabe
# qué significa esto, solo ve "una petición POST".
maintenance_events_created = meter.create_counter(
    name="car_maintenance_events_created_total",
    description="Eventos de mantenimiento creados",
)


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
    maintenance_events_created.add(1)
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

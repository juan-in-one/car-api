import uuid

from fastapi import Depends, FastAPI, HTTPException
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import make_asgi_app
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import engine, get_db, init_db
from app.models import MaintenanceEvent
from app.schemas import MaintenanceEventCreate, MaintenanceEventOut

app = FastAPI(title=settings.app_name)

# Identifica el servicio tanto en métricas como en trazas — sin esto sale
# "unknown_service", y hace falta para cruzar datos entre las dos.
resource = Resource.create({"service.name": "car-api"})

# Métricas (Fase B) — el exportador de Prometheus expone /metrics en esta
# misma app y puerto; Prometheus las scrapea con su ServiceMonitor propio.
metrics.set_meter_provider(
    MeterProvider(metric_readers=[PrometheusMetricReader()], resource=resource)
)
meter = metrics.get_meter("car-api")

# Trazas (Fase D) — a diferencia de las métricas, aquí no hay nadie
# "scrapeando": el exportador empuja (push) cada traza a Alloy vía OTLP, que
# la reenvía a Tempo. "insecure=True": tráfico interno del clúster, sin TLS.
trace.set_tracer_provider(TracerProvider(resource=resource))
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint="alloy.monitoring.svc.cluster.local:4317", insecure=True)
    )
)

# Auto-instrumentación de FastAPI: genera métricas Y trazas (una por cada
# proveedor que haya configurado arriba) para todas las rutas, sin tocar
# cada endpoint uno a uno. excluded_urls igual que antes.
FastAPIInstrumentor.instrument_app(app, excluded_urls="/health,/metrics")

# Instrumenta también las consultas a Postgres: cada una aparece como un
# span "hijo" dentro de la traza de la petición HTTP que la disparó —
# engine.sync_engine porque la instrumentación engancha eventos de
# SQLAlchemy que viven en el motor síncrono interno, incluso usando el
# engine async por fuera.
SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

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

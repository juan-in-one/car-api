# car-api

Microservicio de la plataforma [juan-in-one](https://github.com/juan-in-one) — mantenimiento del coche
(cambios de aceite, ITV, distribución, kilometraje).

Stack: Python + FastAPI + SQLAlchemy (async) + PostgreSQL. Instrumentado con OpenTelemetry (métricas +
trazas) desde el primer commit.

## Desarrollo local

```bash
cp .env.example .env
docker compose up --build
```

API disponible en `http://localhost:8000` (docs interactivas en `/docs`).

## Tests

```bash
pip install -r requirements-check.txt
pytest --cov=app
```

## Endpoints

- `GET /health`
- `POST /maintenance-events`
- `GET /maintenance-events`
- `GET /maintenance-events/{id}`
- `DELETE /maintenance-events/{id}`

## CI/CD

- **`pr-checks.yml`** corre en cada PR: lint (Ruff), tests con cobertura, Gitleaks, Dependency Review, y un
  build + escaneo de la imagen de prueba que **no puede publicar nada** — no hay ni login a GHCR en ese
  workflow.
- **`ci.yml`** corre solo al fusionar a `main`: los mismos escaneos (bloqueantes: Trivy, Semgrep, ZAP),
  build, firma de la imagen con Cosign (keyless) + SBOM con Syft, y publicación en GHCR.
- `main` está protegida: solo se puede fusionar vía PR desde una rama `feat/*`, con los checks de arriba en
  verde.

Ver [juan-in-one/.github](https://github.com/juan-in-one/.github) para el workflow reutilizable completo, y
el [README de la organización](https://github.com/juan-in-one) para la arquitectura de toda la plataforma
(GitOps, cadena de suministro firmada, observabilidad).

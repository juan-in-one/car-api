# car-api

Microservicio de la plataforma [juan-in-one](https://github.com/juan-in-one) — mantenimiento del coche
(cambios de aceite, ITV, distribución, kilometraje).

Parte del stack de aprendizaje DevOps/DevSecOps/GitOps: Kubernetes + Helm + GitHub Actions (CI) + ArgoCD (CD)
sobre un clúster local en OrbStack.

Stack: Python + FastAPI + SQLAlchemy (async) + Postgres



## Estado

v0 — API funcional en local con Docker Compose. Aún sin Helm/CI/CD (llega en los siguientes pasos del
roadmap, ver `wiki/projects/juan-in-one.md` en el vault).

## Desarrollo local

```bash
cp .env.example .env
docker compose up --build
```

API disponible en `http://localhost:8000` (docs interactivas en `/docs`).

## Endpoints

- `GET /health`
- `POST /maintenance-events`
- `GET /maintenance-events`
- `GET /maintenance-events/{id}`
<!-- prueba real: ci y pr-checks separados -->

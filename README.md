# FitnessTracker — Python microservices edition

A rebuild of the original ASP.NET Core FitnessTracker demo as a **Python microservices
architecture**, using FastAPI, PostgreSQL (database-per-service), and Docker Compose.

## Architecture

```
                         ┌─────────────┐
                         │   Browser   │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │   Gateway   │  nginx, routes /api/* to services,
                         │  (port 8080)│  serves the static frontend at /
                         └──────┬──────┘
              ┌─────────┬───────┼────────┬────────────┐
              ▼         ▼       ▼        ▼             ▼
        ┌─────────┐┌─────────┐┌────────┐┌───────────┐┌────────────┐
        │  auth-  ││workout- ││ meal-  ││calculator-││ dashboard- │
        │ service ││service  ││service ││ service   ││ service    │
        │ :8000   ││:8000    ││:8000   ││:8000      ││:8000       │
        └────┬────┘└────┬────┘└───┬────┘└───────────┘└─────┬──────┘
             │          │         │       (stateless,       │ calls the
             ▼          ▼         ▼        no DB)            │ 3 services
        ┌─────────┐┌─────────┐┌────────┐                     │ above over
        │ authdb  ││workoutdb││ mealdb │                     │ HTTP to
        └─────────┘└─────────┘└────────┘                     │ build one
                    Postgres (one instance, one DB per service) response
```

- **auth-service** — registration, login, JWT issuance, user profile. Owns `authdb`.
- **workout-service** — CRUD for workouts. Owns `workoutdb`.
- **meal-service** — CRUD for meals. Owns `mealdb`.
- **calculator-service** — BMI / calorie calculators. Stateless, no database.
- **dashboard-service** — orchestrator: fans out to auth/workout/meal services over
  HTTP and merges the results into one dashboard payload. Has no database of its own.
- **gateway** — nginx reverse proxy; the only port exposed to the outside world.
  Routes `/api/auth/*`, `/api/workouts*`, `/api/meals*`, `/api/calculator/*`,
  `/api/dashboard` to the matching service, and everything else to `frontend`.
- **frontend** — static HTML/JS/Bootstrap single-page app, served by its own nginx
  container, calling the gateway's `/api/*` routes.

**Auth pattern:** auth-service issues a JWT signed with a shared `JWT_SECRET`. Every
other service verifies that JWT *locally* (no network call back to auth-service needed
to authenticate a request) — the standard stateless-auth pattern for microservices.

**Why one Postgres container instead of five:** simpler to run locally. Each service
still only ever connects to its own database (`authdb`, `workoutdb`, `mealdb`) via its
own `DATABASE_URL` — that's what "database per service" actually means. In a real
deployment you'd typically give each service its own managed Postgres instance instead.

## Running it

```bash
cp .env.example .env      # edit JWT_SECRET at least
docker compose up --build
```

Then open **http://localhost:8080**.

Each service also exposes interactive API docs directly (for local debugging, bypass
the gateway): e.g. `docker compose exec auth-service` isn't needed — just add
`ports: ["8001:8000"]` etc. to docker-compose.yml for any service you want to poke at
directly with Swagger UI at `/docs`.

## Project layout

```
fitnesstracker-microservices/
├── docker-compose.yml
├── .env.example
├── gateway/nginx.conf
├── db-init/init-databases.sh       # creates authdb / workoutdb / mealdb on first boot
├── services/
│   ├── auth-service/               # FastAPI + SQLAlchemy + Postgres + JWT
│   ├── workout-service/            # FastAPI + SQLAlchemy + Postgres
│   ├── meal-service/               # FastAPI + SQLAlchemy + Postgres
│   ├── calculator-service/         # FastAPI, stateless
│   └── dashboard-service/          # FastAPI, httpx fan-out aggregator
└── frontend/                       # static HTML/JS/Bootstrap SPA + nginx
```

## What changed vs. the original .NET app

| Original (.NET) | This version |
|---|---|
| Single MVC app, server-rendered Razor views | 5 independent FastAPI services + a static JS frontend |
| In-memory `DataStore` + Session | Postgres, one database per service |
| Session cookie holds login state | Stateless JWT, verified independently by each service |
| One process, one deploy unit | Each service builds, deploys, and scales independently |
| Direct method calls between features | Dashboard aggregates via HTTP calls to other services |

## Notes / next steps if you take this further

- Add a real API gateway (Kong, Traefik) instead of hand-written nginx routes if you
  need rate limiting, auth at the edge, etc.
- Add health-check-based service discovery instead of hardcoded `service-name:8000`
  DNS names (Docker Compose's built-in DNS is fine for this scale, but won't scale to
  Kubernetes-style dynamic instances without a registry).
- Add Alembic migrations instead of `Base.metadata.create_all()` for real schema
  evolution.
- Add an events layer (e.g. RabbitMQ) if dashboard-service's synchronous fan-out
  becomes a latency/availability problem — it currently fails the whole dashboard
  request if any one upstream service is down.

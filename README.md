# 01_backend_systems

Built by [VisionQuantech](https://visionquantech.com) — AI agents, apps & tools for small businesses.

> Python ERP-style backend system built around Domain-Driven Design, Clean Architecture, FastAPI, PostgreSQL, RBAC, and migration-driven delivery.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Custom%20Commercial-orange)](./LICENSE)

This repository is an ERP-style backend foundation demonstrating enterprise patterns in a practical Python stack. The system is organized around domain-driven design, clean architecture boundaries, secure auth, RBAC, order and inventory workflows, and migration-based database evolution.

The project is designed to serve as a strong backend blueprint for internal tooling, SaaS operations, business systems, and domain-heavy service development.

## What this project includes

- FastAPI service layer with API routes and Pydantic schemas
- domain-driven architecture with entities, aggregates, and value objects
- RBAC-based authorization model
- PostgreSQL integration with Alembic migrations
- environment-based configuration for dev and deployment workflows
- structured project layout for future extension into ERP modules
- tests and example data for local validation

## Repository structure

```text
01_backend_systems/
├── .env.example
├── .github/
├── alembic/
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── README.md
├── pyproject.toml
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   ├── services/
│   │   └── value_objects/
│   ├── application/
│   │   └── services/
│   ├── infrastructure/
│   │   ├── database/
│   │   └── repositories/
│   ├── presentation/
│   │   ├── routes/
│   │   └── schemas/
│   └── main.py
├── tests/
├── example_data/
└── README.md
```

## System goals

This backend is built to model a business-operational system with clear responsibilities across layers:

- presentation: API requests and response serialization
- application: business logic and orchestration
- domain: core business rules and entities
- infrastructure: database, persistence, and external integrations

This split is ideal for ERP-like systems, internal business automation, and multi-module platform backends.

## Core domain capabilities

The repository describes a typical enterprise domain, including:

- organizations
- users and auth flows
- inventory management
- orders and fulfillment logic
- invoices and financial workflows
- role-based access control

## Architecture overview

```text
┌──────────────────────────────────────────────────────────────────────┐
│                       Presentation Layer                              │
│  FastAPI routes, request/response schemas, DTOs                     │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       Application Layer                               │
│  use cases, orchestration logic, domain service coordination         │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Domain Layer                                  │
│  entities, value objects, aggregates, business rules                 │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                              │
│ repositories, DB access, integrations, session management            │
└──────────────────────────────────────────────────────────────────────┘
```

## Quick start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ for production-style local validation
- Docker and Docker Compose for containerized setup

### Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### Configure environment

Copy the example environment file and set your values:

```bash
cp .env.example .env
```

Example environment values:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/erp_db
SECRET_KEY=change-this-to-a-secure-random-string-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
```

### Run database migrations

```bash
alembic upgrade head
```

### Start the API server

```bash
uvicorn src.main:app --reload --port 8000
```

### Open API documentation

Once running, open:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker workflow

A Docker Compose file is included for quick container-based local startup:

```bash
docker compose up --build
```

## Testing

Run the test suite with:

```bash
pytest tests/
```

With coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## RBAC model

The project includes a role-based access pattern commonly used in enterprise systems.

| Role | Access level |
| --- | --- |
| admin | full system access |
| manager | team-scoped read/write access |
| operator | limited operational access |
| viewer | read-only access |

This is useful for internal business systems, operations portfolios, and privacy-sensitive apps.

## Typical API surface

The project exposes business-oriented endpoints such as:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | /api/v1/auth/login | user authentication |
| GET | /api/v1/users | list users |
| POST | /api/v1/orders | create order |
| GET | /api/v1/inventory | list inventory |
| GET | /health | health check |

## Production-readiness assessment

### Current maturity: functional backend blueprint

This repository is a strong internal-system starter and a useful DDD reference project, but it should still be treated as a foundation, not a complete enterprise platform out of the box.

### Strengths

- clear layered architecture
- domain-focused vocabulary and structure
- FastAPI-based service simplicity
- PostgreSQL + migration support
- secure auth and RBAC patterns included
- environment-driven configuration is clean and practical

### Risks and gaps before production use

1. Add request validation and audit logging at the edge and domain layers.
2. Harden authentication, token rotation, and session invalidation flows.
3. Define explicit tenant isolation or multi-tenancy rules if needed.
4. Add strict DB migration governance and database backup policies.
5. Introduce tracing, metrics, and structured logging for operational visibility.
6. Add rate limiting, CORS hardening, and security headers in production settings.
7. Validate app behavior under real concurrency, failure, and edge-case business workflows.
8. Add dependency scanning, container scanning, and CI enforcement for release discipline.

## Security considerations

This repository includes auth and config patterns that are useful for enterprise work, but production deployments should add stronger controls:

- rotate secret keys and production credentials regularly
- validate `ALLOWED_ORIGINS` and environment-sensitive policy settings
- treat logs and error responses carefully to avoid leaking internals
- enforce strict input validation and business authorization checks
- use secure database credentials and secret management
- separate development and production configuration strongly

## Licensing note

This repository contains a custom commercial license in `LICENSE`.

Important: the project metadata in GitHub may report MIT, but the actual repository license file is the custom commercial license. Before using this code in a commercial, enterprise, or revenue-generating scenario, review the license file directly and confirm the allowed usage rights.

## Monetization opportunities

This backend architecture is well-suited for several monetization patterns.

| Business model | Best use case |
| --- | --- |
| B2B SaaS backend | internal business software and workflow platforms |
| white-labeled ERP base | enterprise vertical deployments |
| custom software services | client-specific business systems |
| platform starter kit | internal product teams and agencies |
| managed hosting | teams who want secure deployment without building from scratch |

### Practical paths

- sell hosted business workflow services
- use this as a backend base for a vertical SaaS product
- offer enterprise customization, migration, and implementation work
- package the backend as a professional starter for small businesses or operations teams

## GitHub discoverability

This repo should be positioned around terms such as:

- Python ERP backend
- DDD backend architecture
- FastAPI business backend
- enterprise backend template
- Python RBAC system
- PostgreSQL Alembic backend starter
- domain-driven design Python project

To improve visibility:

- keep the description precise and domain-specific
- emphasize enterprise backend use cases and architecture quality
- document business modules and extension points clearly
- add a workload-focused architecture diagram
- provide real example use cases and screenshots where possible

## Roadmap ideas

- add explicit authentication and authorization tests
- introduce tenant or organization isolation patterns
- add invoice and finance module flows
- expand inventory and order lifecycle management
- include CI pipeline with linting, tests, and security checks
- add OpenAPI schema versioning and contract discipline
- implement metrics, tracing, and health-gate checks

## Contributing

Contributions are welcome if they improve:

- correctness and robustness
- DDD alignment and code clarity
- security and validation patterns
- testing quality and migration safety
- developer onboarding and documentation quality

## License

See the repository `LICENSE` file for the full legal terms.
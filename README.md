# 01_backend_systems - ERP-Style Backend

> Production-grade ERP backend demonstrating Domain-Driven Design, Clean Architecture, and enterprise patterns.

## 🎯 Overview

This module implements a comprehensive ERP-style backend with:

- **Domain-Driven Design (DDD)** - Entities, Value Objects, Aggregates
- **Clean Architecture** - Layered separation of concerns
- **RBAC** - Role-based access control
- **RESTful APIs** - OpenAPI 3.0 documented
- **PostgreSQL** - With Alembic migrations

## 📁 Structure

```
01_backend_systems/
├── src/
│   ├── domain/           # Business logic & entities
│   │   ├── entities/     # Core domain models
│   │   └── value_objects/# Immutable value types
│   ├── application/      # Use cases & services
│   │   └── services/     # Application services
│   ├── infrastructure/   # External concerns
│   │   ├── database/     # DB connection & session
│   │   └── repositories/ # Data access layer
│   └── presentation/     # API layer
│       ├── routes/       # API endpoints
│       └── schemas/      # Pydantic models
├── alembic/              # Database migrations
├── tests/                # Unit & integration tests
└── example_data/         # Sample data for testing
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or use SQLite for development)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e .

# Set environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start the server
uvicorn src.main:app --reload --port 8000
```

### API Documentation

Once running, visit:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                      │
│  (FastAPI Routes, Pydantic Schemas, Request/Response DTOs)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                       │
│     (Use Cases, Application Services, Business Logic)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       DOMAIN LAYER                          │
│   (Entities, Value Objects, Domain Services, Aggregates)    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                      │
│    (Repositories, Database, External APIs, Messaging)       │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Domain Model

The ERP system manages:

- **Organizations** - Multi-tenant company management
- **Users** - Authentication and authorization
- **Inventory** - Product and stock management
- **Orders** - Sales order processing
- **Invoices** - Billing and payment tracking

## 🔒 RBAC Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full system access |
| `manager` | Read/write on assigned resources |
| `operator` | Limited write access |
| `viewer` | Read-only access |

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_entities.py -v
```

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Authenticate user |
| GET | `/api/v1/users` | List users |
| POST | `/api/v1/orders` | Create order |
| GET | `/api/v1/inventory` | List inventory |
| GET | `/health` | Health check |

## 🔧 Configuration

Environment variables (`.env`):

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/erp_db
SECRET_KEY=your-secret-key-here
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 📄 License

MIT

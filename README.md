# BigO Academy

A microservices-based learning management system built to digitize and scale the operations of [A2SV (Africa to Silicon Valley)](https://a2sv.org) — a program that trains African university students in software engineering and places them at top tech companies worldwide.

---

## What This Project Does

A2SV runs a rigorous multi-year software engineering curriculum. Managing hundreds of students across cohorts, tracking attendance, monitoring contest performance, processing monthly payments, and surfacing at-risk students — all of this was done manually. BigO Academy replaces that with a production-grade platform built on modern software engineering principles.

The system handles:
- Student and teacher account management with role-based access control
- Cohort lifecycle management (enrollment, promotion, graduation)
- Curriculum delivery with topic and problem tracking
- Attendance recording and percentage calculation
- Contest result submission and leaderboard ranking
- Monthly subscription payments with admin verification workflow
- Real-time analytics including performance scores, consistency metrics, and at-risk detection

---

## Architecture

BigO Academy is a distributed system of four independently deployable services that communicate over Kafka for event-driven workflows and expose REST APIs for synchronous operations.

```
┌─────────────────┐     ┌──────────────────┐
│   Auth Service  │     │ Academic Service  │
│                 │     │                  │
│  - Registration │     │  - Students      │
│  - Login / JWT  │     │  - Teachers      │
│  - OAuth        │     │  - Cohorts       │
│  - OTP / Reset  │     │  - Curriculum    │
└────────┬────────┘     │  - Attendance    │
         │              │  - Contests      │
         │ JWT tokens   │  - Warnings      │
         │ shared via   │  - Mentorship    │
         │ secret key   └────────┬─────────┘
         │                       │
         │              Kafka Events
         │              (problem.solved,
         │               attendance.updated,
         │               warning.issued, ...)
         │                       │
┌────────▼────────┐     ┌────────▼─────────┐
│ Payment Service │     │Analytics Service  │
│                 │     │                   │
│  - Student fees │     │  - Leaderboard    │
│  - Teacher pay  │     │  - Performance    │
│  - Verification │     │  - At-risk detect │
│  - Reports      │     │  - Historical     │
└─────────────────┘     └───────────────────┘
```

Every service uses **hexagonal architecture** (ports and adapters): domain logic is pure Python with zero framework dependencies, application use cases orchestrate business flows, and adapters connect to Django ORM, Kafka, and DRF at the edges.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Web Framework | Django 4.x + Django REST Framework |
| Database | PostgreSQL (one per service) |
| Message Broker | Apache Kafka |
| Authentication | JWT (PyJWT) — issued by Auth Service, validated independently |
| Background Jobs | Celery + Redis |
| Architecture | Hexagonal (Ports and Adapters) |
| Testing | pytest + Django TestCase |

---

## Services

### Auth Service
Owns user identity across the platform. Issues JWT access tokens (15 min) and refresh tokens (7 days). All other services validate tokens independently using a shared secret — no round-trips back to Auth.

Supports registration, login, OAuth (Google/GitHub), OTP-based password reset, and admin account management.

### Academic Service
The operational core. Manages the full student lifecycle from enrollment through graduation. Publishes Kafka events on every meaningful state change — problem solved, attendance recorded, warning issued — so downstream services stay in sync without coupling.

### Payment Service
Handles the monthly subscription model for students (500 ETB/month) and salary processing for teachers. Students submit payment references after paying externally; admins verify and update status. Enforces strict status transitions (PENDING → PAID/FAILED/OVERDUE only).

### Analytics Service
A read-only service that derives insights from Academic Service events. Maintains a live leaderboard, tracks historical performance snapshots, identifies at-risk students, and exposes aggregated cohort and platform metrics for admin dashboards. Updated via Kafka — no direct HTTP writes.

---

## Project Structure

```
BigO_Academy/
├── auth-service/
│   ├── domain/           # User model, enums, exceptions
│   ├── application/      # 15 use cases, outbound ports
│   ├── adapters/         # DRF views, Django ORM, JWT, Email
│   ├── infrastructure/   # Dependency wiring
│   └── tests/            # 68 unit tests + integration tests
│
├── academic-service/
│   ├── domain/           # 13 models, enums, exceptions
│   ├── application/      # 43 use cases, 11 outbound ports
│   ├── adapters/         # DRF views, Django ORM, Kafka producer
│   ├── infrastructure/   # Dependency wiring
│   └── tests/            # 141 unit tests + 32 integration tests
│
├── payment-service/
│   ├── domain/           # StudentPayment, TeacherPayment models
│   ├── application/      # 14 use cases, 4 outbound ports
│   ├── adapters/         # DRF views, Django ORM, Kafka publisher
│   ├── infrastructure/   # Dependency wiring
│   └── tests/            # 54 unit tests + 8 integration tests
│
└── analytics-service/
    ├── domain/           # Analytics models, enums, exceptions
    ├── application/      # 9 read use cases + 7 Kafka use cases
    ├── adapters/         # DRF views, Django ORM, Kafka consumers
    ├── infrastructure/   # Dependency wiring, Celery jobs
    └── tests/            # 34 integration tests
```

---

## Test Coverage

| Service | Unit Tests | Integration Tests | Total |
|---|---|---|---|
| Auth | 68 | ✅ | 68+ |
| Academic | 141 | 32 | 173+ |
| Payment | 54 | 8 | 62+ |
| Analytics | — | 34 | 34+ |
| **Total** | **263** | **74+** | **337+** |

Unit tests use in-memory fake repositories — zero Django or database dependencies. Integration tests hit a real PostgreSQL test database via Django's test client.

---

## Running Locally

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Apache Kafka + Zookeeper
- Redis (for Analytics Service Celery jobs)

### Quick start with Docker

```bash
# Start Postgres, Kafka, Zookeeper, Redis
docker-compose up -d
```

### Per-service setup

Each service is an independent Django project. Run these steps for each:

```bash
cd auth-service          # or academic-service, payment-service, analytics-service

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in DB credentials and JWT_SECRET_KEY
# JWT_SECRET_KEY must be identical across all services

python manage.py migrate
python manage.py runserver 8000   # use 8001, 8002, 8003 for other services
```

### Running tests

```bash
# Unit tests (no database required)
pytest tests/use_cases/ -v

# Integration tests (requires PostgreSQL)
pytest tests/integration/ -v --ds=config.test_settings
```

### Starting Kafka consumers (Analytics Service)

```bash
cd analytics-service
python manage.py run_consumers
```

### Starting Celery (Analytics Service)

```bash
celery -A config worker -l info
celery -A config beat -l info
```

---

## Key Design Decisions

**Hexagonal Architecture** — Every service separates domain logic from infrastructure. Use cases depend on abstract ports (Python ABCs); adapters implement them. This makes business logic testable without a database, and makes infrastructure swappable without touching business rules.

**JWT without Auth Service round-trips** — Each service decodes tokens independently using a shared `JWT_SECRET_KEY`. This avoids a network dependency on Auth Service for every authenticated request.

**Event-driven Analytics** — The Analytics Service never calls other services over HTTP. It reacts to Kafka events from Academic Service and builds derived views (leaderboards, performance scores, at-risk lists) asynchronously. This keeps services loosely coupled and the analytics always current.

**Fake repositories for unit tests** — Every service has a `tests/fakes.py` with in-memory implementations of all repository ports. Use cases are tested against fakes — fast, deterministic, and infrastructure-free. Integration tests then verify the real adapters work against PostgreSQL.

**Status transition enforcement in the domain** — Payment status transitions (PENDING → PAID/FAILED/OVERDUE) and student status transitions (ACTIVE → PROBATION → DROPPED etc.) are enforced by `can_transition_to()` methods on domain models, not in views or use cases. Business rules live in the domain where they belong.

---

## Team

Built by a team of 2 software engineering students, with a clean split between domain/application layer (business logic, ports, use cases, tests) and adapter/infrastructure layer (Django ORM, DRF views, Kafka wiring).

---

*BigO Academy is named after the Big O notation — the language of algorithmic thinking that every A2SV student masters.*
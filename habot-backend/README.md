# HABOT Connect Backend

**Candidate:** Jaya Kishore Siripurapu  
**Position:** Python Backend Developer  
**Email:** `<your-email>`  
**Project:** HABOT Connect Backend

This is the backend for the HABOT Connect hiring project. It is a Django + Django REST Framework project that helps a mock Parent pick an LSA, check available time slots, create a booking, and process a mock HTTP payment flow. The project is intentionally scoped around the backend logic rather than user registration or real authentication.

The project is built to show the actual engineering work behind a hiring assignment: database design, API validation, booking rules, payment simulation, concurrency protection, query optimization, testing, and technical documentation.

---

# 1. Project Overview

The app models a very simple marketplace flow:

- A Parent is created in Django Admin.
- An LSA profile is created in Django Admin.
- Skills are created and linked to an LSA.
- Availability slots are created for the LSA.
- A client searches LSAs by skill, experience, rating, rate, or date.
- A Parent picks an available slot and creates a booking.
- The booking creates an initiated payment record.
- A mock payment result confirms or fails the booking.
- The system updates the booking status and the slot status.

This is not a full user-authenticated product. The requirement for the hiring project was to build a backend prototype that demonstrates database relationships, API design, booking and payment flow, automated testing, and optimization. The repository stays within that scope and does not add JWT, OAuth, registration, or login flows.

The main business entities are:

- Parent
- LSA Profile
- Skill
- LSA Skill relationship
- Availability
- Booking
- Payment

The project also includes a health check, OpenAPI schema, Docker setup, and CI workflow.

---

# 2. Requirements From the Hiring Project

| Hiring requirement | Actual implementation in this repo |
| --- | --- |
| Parent / LSA schema | `apps.parents.models.Parent`, `apps.lsas.models.LSAProfile`, `Skill`, `LSASkill`, `Availability` |
| Booking API | `POST /api/v1/bookings/`, `GET /api/v1/bookings/<uuid:pk>/`, `POST /api/v1/bookings/<uuid:pk>/cancel/` |
| LSA search | `GET /api/v1/lsas/search/` with skill, experience, rating, date, hourly rate filters |
| Mock external service | `POST /api/v1/payments/process/` calls `/mock-payment-gateway/payments/` over HTTP using Python `requests`; `/api/v1/payments/webhook/` remains idempotent |
| N+1 optimization | `lsa_queryset()` uses `Prefetch` and `select_related` and the test verifies constant 2-query search |
| Automated tests | `pytest` suite in `tests/` with 35 passing tests |
| GitHub Actions | `.github/workflows/tests.yml` runs build + migration + pytest |
| Technical README | This document |
| Database relations | Django models with FK, unique constraints, indexes, check constraints, and PostgreSQL trigger |
| Booking validation | Availability checks, duplicate booking protection, invalid dates and invalid booking status |

This project is a bit bigger than the minimum spec because it also includes parent dashboard, booking history, slot schedule, health checks, Swagger/OpenAPI, request ID middleware, standardized response envelopes, and query hardening tests.

---

# 3. Features

## Parent Features

- Parent records are created through Django Admin.
- Parent list and detail are available through:
  - `GET /api/v1/parents/`
  - `GET /api/v1/parents/<uuid:pk>/`
- Parent booking history is available via:
  - `GET /api/v1/parents/<uuid:pk>/bookings/`
- Parent dashboard summary is available via:
  - `GET /api/v1/parents/<uuid:pk>/dashboard/`
- Parent dashboard returns counts for total bookings, upcoming, completed, cancelled, and failed.

## LSA Features

- LSA profiles include name, bio, experience, hourly rate, rating, and active status.
- Skills are stored separately and linked to an LSA through `LSASkill`.
- LSAs can be searched by:
  - `skill`
  - `experience`
  - `rating`
  - `available_date`
  - `hourly_rate_max`
- Search endpoint returns a compact summary with skills and rates.
- LSA detail endpoint returns full profile data.
- Availability endpoint returns active slots for a specific LSA.

## Booking Features

- A Parent can create a booking for an available LSA slot.
- The booking automatically creates a payment record.
- The availability slot is marked as `BOOKED` when the booking is created.
- Duplicate booking attempts on the same slot fail with a validation error.
- Bookings can be retrieved and cancelled.
- Cancelled bookings release the slot back to `AVAILABLE`.

## Payment Features

- Payment uses a mock HTTP gateway, not a real production gateway.
- Payment records have statuses: `INITIATED`, `SUCCESS`, `FAILED`.
- `POST /api/v1/payments/process/` sends a real HTTP request through Python `requests`.
- `/mock-payment-gateway/payments/` is the lightweight mock external payment service.
- `POST /api/v1/payments/webhook/` accepts the same normalized payload that a real gateway would send.
- Payment processing is idempotent once a payment reaches a terminal state.

## Backend Features

- Request ID middleware adds `X-Request-ID` to every response.
- Custom response envelope wraps success and error objects.
- Custom exception handling returns consistent error payloads.
- Health checks verify app liveliness and database readiness.
- Docker-first setup for local development.
- Swagger/OpenAPI schema is exposed.
- Automated tests cover business logic and API contracts.

---

# 4. Technology Stack

| Category | Technology |
| --- | --- |
| Language | Python 3.12 |
| Framework | Django 5.2.4 |
| API framework | Django REST Framework 3.16.0 |
| Database | PostgreSQL / Neon-ready |
| Database driver | `psycopg[binary]` 3.2.9 |
| Environment config | `django-environ` 0.12.0 |
| API docs | `drf-spectacular` 0.28.0 |
| ASGI/WSGI server | Gunicorn 23.0.0 |
| Static files | WhiteNoise 6.9.0 |
| CORS | django-cors-headers 4.7.0 |
| Containerization | Docker |
| Testing | pytest 8.4.1, pytest-django 4.11.1 |
| CI | GitHub Actions |

The project is designed to run with PostgreSQL in production-like environments, while the test settings use SQLite in-memory for isolated, fast tests.

---

# 5. Why Django + Django REST Framework?

I chose Django because the project is data-heavy and relation-heavy. We have Parent, LSA, Availability, Booking, Payment and the skill relationship. Django ORM makes those relations straightforward, and the admin interface is useful for creating mock profiles without building a registration system.

I used Django REST Framework because the project is an API-first backend. The main work is not HTML pages; it is JSON payloads, request validation, status codes, error handling, and serializer-based responses. DRF fits that much better than building custom JSON views by hand.

In this project, the Django MVT structure is slightly different from a traditional template app because the main output is JSON. The Model layer is still the database model. The View layer is the DRF API view. The Template part is mostly not used because this is not a server-rendered project. The serializers are the layer that control how model data becomes API output, and that sits naturally in the DRF side of the architecture.

Django Admin was useful because the project explicitly says there is no user auth flow. Instead of building registration, I used the admin panel to create mock Parent and LSA records. That keeps the backend focused on the hiring project: booking, search, payment, and optimization.

---

# 6. Django MVT vs Flask MVC

## Django MVT

In Django, the idea is:

- Model: database structure and ORM
- View: HTTP logic and request handling
- Template: HTML rendering

This project is an API backend, so the Template layer is not the main focus. The actual flow is:

- `models.py` defines data models
- `serializers.py` transforms data to and from JSON
- `views.py` handles API requests
- `services.py` contains business logic like booking creation and payment processing
- `urls.py` wires endpoints to views

This gives a clean structure without making the project overly complicated.

## Flask MVC

In Flask, a similar pattern would look like:

- Models: SQLAlchemy models
- Controllers: route handlers
- Services: business logic
- JSON responses: custom response payloads

That would also work, but in this project the Django stack is more natural because of:

- built-in admin for mock data
- mature ORM relations
- migration management
- serializers for API output
- easier test setup with pytest and Django test client

For this assignment, Django was the better fit because the project expects database relationships, migration discipline, and Django-based API design.

---

# 7. Architecture

```text
                    Client / Postman / Frontend
                           |
                           v
                 Django REST Framework
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
      Parents API      LSAs API       Bookings API
          |                |                |
          |                +--------+-------+
          |                         |
          v                         v
     Parent Dashboard         Payment API / Webhook
                                    |
                                    v
                             Booking status updates
                                    |
                                    v
                           PostgreSQL / Neon
```

The main architecture is straightforward:

- API layer handles HTTP requests
- Serializer layer validates request payloads and formats data
- Service layer handles booking and payment logic
- ORM handles queries and transactions
- PostgreSQL keeps the relational data and concurrent locking safe

---

# 8. Application Architecture

```text
backend/
├── apps/
│   ├── common/
│   │   ├── exceptions.py
│   │   ├── middleware.py
│   │   ├── responses.py
│   │   └── ...
│   ├── parents/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── lsas/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── bookings/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   └── views.py
│   └── payments/
│       ├── models.py
│       ├── serializers.py
│       ├── services.py
│       ├── urls.py
│       └── views.py
├── config/
│   ├── settings/
│   ├── urls.py
│   └── wsgi.py
├── requirements/
├── manage.py
├── tests/
├── staticfiles/
├── pytest.ini
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

Important pieces:

- `apps.parents` contains Parent model and parent dashboard APIs.
- `apps.lsas` contains LSA, Skill, LSASkill, Availability models and LSA search.
- `apps.bookings` contains Booking model, booking workflows, and transaction locking.
- `apps.payments` contains Payment model and mock gateway processing.
- `apps.common` includes custom response format, request ID middleware, and error handling.
- `config.settings` contains environment-based settings for development, production, and tests.

---

# 9. Request Lifecycle

```text
HTTP Request
     |
     v
URL Router
     |
     v
APIView / DRF View
     |
     v
Serializer validation
     |
     v
Service layer
     |
     v
Django ORM / database transaction
     |
     v
Database writes / locks / constraints
     |
     v
Response serializer / JSON payload
```

The common middleware adds `X-Request-ID` and sets a request context value for logging. The custom exception handler normalizes DRF validation and unexpected errors into a standard envelope.

The `apps.common.responses` module wraps both successful and failed API responses in a consistent JSON structure.

---

# 10. Business Flow

The intended flow is simple and consistent with the project scope:

```text
Django Admin
   |
   +--> Create Parent
   |
   +--> Create LSA
   |
   +--> Create Skills
   |
   +--> Assign Skills to LSA
   |
   +--> Create Availability Slots
   |
   v
Search LSAs by skill / date / rate / rating
   |
   v
Parent chooses an available slot
   |
   v
POST /api/v1/bookings/
   |
   +--> create Booking (PAYMENT_PENDING)
   +--> create Payment (INITIATED)
   +--> mark Availability as BOOKED
   |
   v
POST /api/v1/payments/process/ or /webhook/
   |
   +--> success => booking CONFIRMED, payment SUCCESS
   +--> failure => booking FAILED, slot AVAILABLE
   |
   v
Parent dashboard / booking history / status fetch
```

The important design choice is that there is no user registration or auth layer. The application assumes you already have a mock Parent and mock LSA in the database and that the client selects by ID.

---

# 11. Database Design

## Parent

`apps.parents.models.Parent`

Fields:

- `id` (UUID primary key)
- `full_name`
- `email` (unique)
- `phone`
- `city`
- `created_at`
- `updated_at`

Purpose:

- Represents the parent profile using the app.
- Parent is used as the booking owner.

## LSA Profile

`apps.lsas.models.LSAProfile`

Fields:

- `id`
- `full_name`
- `bio`
- `experience_years`
- `hourly_rate`
- `rating`
- `is_active`
- `created_at`
- `updated_at`

Notes:

- `rating` is checked to be between 0 and 5.
- `is_active` is indexed and used for filtering.

## Skill

`apps.lsas.models.Skill`

Fields:

- `id`
- `name` (unique)
- `category`
- `description`

Purpose:

- Keeps skill names normalized instead of repeating text in each LSA record.

## LSA Skill relationship

`apps.lsas.models.LSASkill`

Fields:

- `id`
- `lsa`
- `skill`
- `experience_years`

Constraints:

- unique combination of `(lsa, skill)`

This prevents the same skill from being duplicated for the same LSA.

## Availability

`apps.lsas.models.Availability`

Fields:

- `id`
- `lsa`
- `date`
- `start_time`
- `end_time`
- `status`

Status choices:

- `AVAILABLE`
- `BOOKED`
- `BLOCKED`

Important rules:

- `start_time` must be less than `end_time`
- there is a PostgreSQL trigger to prevent overlapping availability slots for the same LSA

## Booking

`apps.bookings.models.Booking`

Fields:

- `id`
- `parent`
- `availability`
- `status`
- `created_at`
- `updated_at`

Status choices:

- `PENDING`
- `PAYMENT_PENDING`
- `CONFIRMED`
- `FAILED`
- `CANCELLED`
- `COMPLETED`

Important constraints:

- Unique constraint on `availability` so only one booking can exist per slot

## Payment

`apps.payments.models.Payment`

Fields:

- `id`
- `booking`
- `gateway_reference`
- `amount`
- `status`
- `transaction_time`

Status choices:

- `INITIATED`
- `SUCCESS`
- `FAILED`

---

# 12. Entity Relationship Diagram

```text
Parent
  |
  | 1 --- many
  v
Booking -------------------< Payment
  |                            |
  | many to one                | many to one
  v                            v
Availability -----------------< LSAProfile
  |                               |
  | many to one                   | 1 --- many
  v                               v
LSASkill --------------------> Skill
  |
  | many to one
  v
LSAProfile
```

More specifically:

- A Parent can have many Bookings.
- An Availability slot belongs to one LSA and can have one Booking.
- One LSA has many Availability slots.
- One LSA can have many LSASkill rows.
- One Skill can be assigned to many LSA profiles via LSASkill.
- One Booking can have many Payment records in the model design, though the current service logic uses the latest payment for each booking.

---

# 13. Database Normalization

The database design is normalized enough for this project without becoming over-engineered.

- `Skill` is separated into its own table to avoid storing repeated strings across LSAs.
- `LSASkill` creates the many-to-many relationship between LSA and skill while storing extra data such as the LSA’s experience in that skill.
- `Availability` is separate from `LSAProfile` so each time slot can be managed independently.
- `Booking` stores the relationship between a parent and a slot, rather than repeating slot info on parent or LSA models.
- `Payment` is separate from booking so payment status can be tracked independently and the booking can be evaluated without mixing payment data into one table.

This keeps the data clean. For example, if an LSA’s rate changes later, we do not duplicate that rate in each booked slot or payment row. We also avoid repeating skill names in every LSA record.

---

# 14. PostgreSQL and Neon

The project is set up for PostgreSQL and is designed to work with Neon-managed PostgreSQL. The settings use `DATABASE_URL` from the environment and the project uses `psycopg` for the database driver.

The reason I used PostgreSQL is that this project has several relational entities and transaction-sensitive operations:

- booking creation
- slot locking
- response to payment results
- preventing duplicate bookings
- enforcing constraints on overlapping availability

PostgreSQL is a better fit than SQLite for this type of work because it supports proper transactions, row-level locking, and database constraints. Neon is a good match for a hiring project because it is a managed PostgreSQL service and keeps the application close to a production environment without adding extra setup complexity.

The repo does not expose the actual database URL in documentation. The environment file uses placeholders and the application expects a real Database URL in the environment.

---

# 15. Database Indexing

The actual repository includes these important indexes and constraints:

- `Parent.full_name` is indexed.
- `LSAProfile.full_name` is indexed.
- `LSAProfile.is_active` is indexed.
- `Availability.date` is indexed.
- `Availability.status` is indexed.
- `Availability` has a composite index on `(lsa, date)` named `availability_lsa_date_idx`.
- `Booking.status` is indexed.
- `Payment.status` is indexed.
- `Parent.email` is unique.
- `LSASkill` has a unique constraint on `(lsa, skill)`.
- `Booking` has a unique constraint on `availability`.
- `LSAProfile.rating` has a check constraint for `0 <= rating <= 5`.
- `Availability` has a check constraint that `start_time < end_time`.
- PostgreSQL trigger in migration `0002_prevent_overlapping_availability.py` blocks overlapping slots for the same LSA.

These indexes and constraints are not arbitrary. They support the most common query patterns and keep the business rules consistent.

---

# 16. N+1 Query Problem

## What is N+1?

N+1 happens when a list query loads a parent object and then each item triggers a second query for related data. For example:

- fetch 8 LSAs
- then fetch skill rows for each LSA separately
- result: many small queries instead of a few larger ones

That is slow and not good for API performance.

## How this project avoids it

The project uses a few specific ORM techniques:

- `select_related("lsa")` in availability and booking queries
- `prefetch_related(Prefetch(...))` in `lsa_queryset()`
- `select_related("skill")` for LSA skill fetches
- `distinct()` after building filter conditions
- `annotate(Count("lsa_skills", distinct=True))` for filter support

The actual method is in `apps.lsas.views.lsa_queryset()`:

```python
skills = LSASkill.objects.select_related("skill").order_by("skill__name")
return LSAProfile.objects.prefetch_related(Prefetch("lsa_skills", queryset=skills))
```

This means the LSA search avoids a query per LSA. The test verifies this:

```python
with django_assert_num_queries(2):
    response = client.get("/api/v1/lsas/search/")
```

And the test asserts 8 LSAs are returned in two queries. This is exactly the kind of performance check the company wanted to see in the project.

This matters because the API often has a list of LSAs. A naive implementation would run a lot of extra database round-trips, which is not acceptable in a production-like backend prototype.

---

# 17. Booking Concurrency / Double Booking Protection

This is one of the most important parts of the project.

The booking creation code is in `apps.bookings.services.create_booking()` and it uses:

- `transaction.atomic()`
- `Availability.objects.select_for_update()`
- `Booking.objects.create()` inside the transaction
- a uniqueness constraint on `Booking.availability`

This matters because a race condition can happen:

```text
Parent A and Parent B hit the same availability slot at the same time.
```

If both requests check availability before booking, they can both see `AVAILABLE` and then both try to book. That is a classic double-booking bug.

The code blocks this by locking the availability row before checking the status. The request with the lock proceeds, creates the booking, and marks the slot as `BOOKED`. The second request reaches the same row later, sees the slot is no longer available, and raises validation.

The uniqueness constraint on `Booking.availability` adds an extra protection in the database. Even if code logic misses something, the database still prevents two bookings for one slot.

The API returns a 400 response with a clear message if the slot is already booked.

---

# 18. Booking State Machine

Booking states are defined in `apps.bookings.models.Booking.Status`.

```text
PENDING
  |
  +--> PAYMENT_PENDING
          |
          +--> CONFIRMED (payment success)
          |
          +--> FAILED (payment failure)

CONFIRMED
  |
  +--> CANCELLED

FAILED
  |
  +--> (terminal state)

CANCELLED
  |
  +--> (terminal state)

COMPLETED
  |
  +--> (terminal state)
```

The actual flow used in code is:

- Booking is created with `PAYMENT_PENDING`.
- Payment success sets booking to `CONFIRMED`.
- Payment failure sets booking to `FAILED`.
- Cancellation sets booking to `CANCELLED`.
- `COMPLETED` is defined in the model but is not the primary flow used by the mock API.

The real cancellation restriction in code is that only `PENDING`, `CONFIRMED`, and `PAYMENT_PENDING` bookings can be cancelled.

---

# 19. Payment Integration

The project uses a mock HTTP payment gateway, not a real production payment gateway. The payment service talks to that mock gateway through Python's `requests` library so the integration demonstrates a real external-service boundary with timeout, exception handling, and logging.

## Flow

1. Booking is created with a `Payment` record in `INITIATED` state.
2. Client calls `POST /api/v1/payments/process/`.
3. The payment service gets the latest payment and calls the configured gateway URL with `requests.post(...)`.
4. The mock gateway endpoint `POST /mock-payment-gateway/payments/` returns an approval or rejection result.
5. The existing payment state service applies the result: `success` or `failed`.
6. On success:
   - payment status becomes `SUCCESS`
   - booking status becomes `CONFIRMED`
   - availability remains `BOOKED`
7. On failure:
   - payment status becomes `FAILED`
   - booking status becomes `FAILED`
   - availability becomes `AVAILABLE`

The webhook endpoint remains separate: `POST /api/v1/payments/webhook/` accepts a normalized gateway-style payload and applies it idempotently.

`apply_payment_result()` in `apps.payments.services` is wrapped in `transaction.atomic()` and uses `select_for_update()` to lock the payment, booking, and availability row during processing.

The external HTTP call happens before the lock-protected state transition. That keeps the existing database consistency guarantees without holding row locks while waiting on the mock gateway.

The webhook is idempotent. After a payment reaches a terminal state, repeated terminal-state notifications do not mutate the booking again.

## Gateway Client

`apps.payments.payment_gateway.charge_payment()` is responsible for HTTP communication only:

```text
Payment Process API
  -> Payment Service
  -> Payment Gateway Client
  -> requests.post(...)
  -> /mock-payment-gateway/payments/
  -> Payment Service applies result
```

The gateway URL and timeout are read from environment configuration:

- `PAYMENT_GATEWAY_URL`
- `PAYMENT_GATEWAY_TIMEOUT`

The client handles and logs:

- `requests.exceptions.Timeout`
- `requests.exceptions.ConnectionError`
- `requests.exceptions.HTTPError`
- other `requests.exceptions.RequestException`

These failures are converted into the existing DRF/global exception response envelope with a `503` response. The payment, booking, and availability rows are not mutated when the gateway request fails before a valid payment result is received.

## Hiring Requirement: Mock External Service

The payment integration uses a mock HTTP payment gateway. The application communicates with the gateway through Python's `requests` library. External request failures such as timeout, connection errors, HTTP errors, and unexpected request exceptions are handled and logged without exposing secrets.

---

# 20. API Documentation

The project exposes a small API surface designed around the hiring assignment. Product API routes are under `/api/v1/...`; health endpoints and the mock gateway endpoint are separate. There is no authentication layer in this version; mock Parent and LSA records are selected by ID.

| S. No. | Method | Actual API | Input ID / Body Needed | Output | Goal |
| --- | --- | --- | --- | --- | --- |
| 1 | GET | `/health/` | None | Success envelope with `status: "ok"` and `database: "connected"`, or error envelope with `503` if DB is down | Readiness check for the app and DB. Docker uses this as a health probe. |
| 2 | GET | `/health/live/` | None | Success envelope with `{"status": "ok"}` | Confirms the Django process is running. |
| 3 | GET | `/health/ready/` | None | Same as `/health/` | Explicit readiness endpoint for database availability check. |
| 4 | GET | `/api/v1/parents/` | None | Success envelope with list of parent objects: `[{"id": "...", "full_name": "..."}]` | Return the mock parents available for selection in the app. |
| 5 | GET | `/api/v1/parents/<uuid:pk>/` | `pk` = Parent UUID | Success envelope with the parent profile: `id`, `full_name`, `email`, `city` | Return one parent profile by ID. |
| 6 | GET | `/api/v1/parents/<uuid:pk>/bookings/` | `pk` = Parent UUID; optional query param `status` | Success envelope with booking history and latest payment status | Show booking history for one parent and optionally filter by booking status. |
| 7 | GET | `/api/v1/parents/<uuid:pk>/dashboard/` | `pk` = Parent UUID | Success envelope with counts: `total_bookings`, `upcoming`, `completed`, `cancelled`, `failed` | Return a small dashboard summary for the parent. |
| 8 | GET | `/api/v1/lsas/search/` | Query params: `skill`, `experience`, `rating`, `available_date`, `hourly_rate_max` | Success envelope with list of LSA summaries: `id`, `name`, `rating`, `experience`, `hourly_rate`, `skills` | Search active LSAs based on skill and availability filters. |
| 9 | GET | `/api/v1/lsas/<uuid:pk>/` | `pk` = LSA UUID | Success envelope with LSA profile details: `bio`, `experience`, `rating`, `hourly_rate`, `skills` | Return a single LSA profile and their skills. |
| 10 | GET | `/api/v1/lsas/<uuid:pk>/availability/` | `pk` = LSA UUID | Success envelope with only currently available slots | Return available time slots for one LSA. |
| 11 | GET | `/api/v1/lsas/<uuid:pk>/schedule/` | `pk` = LSA UUID; optional query param `date` | Success envelope with all slot entries for that LSA, including status values | Return the LSA schedule, including booked or blocked slots, optionally filtered by date. |
| 12 | GET | `/api/v1/bookings/` | None | Success envelope with list of bookings and related parent, LSA, slot, and payment details | List all bookings for monitoring and inspection. |
| 13 | POST | `/api/v1/bookings/` | JSON body: `parent_id`, `availability_id` | Success envelope with `booking_id`, `status`, `payment_status`, `availability_id` and `201 Created` | Create a booking, create the initiated payment record, and reserve the availability slot. |
| 14 | GET | `/api/v1/bookings/<uuid:pk>/` | `pk` = Booking UUID | Success envelope with booking detail, parent profile, LSA info, slot, and payment status | Return one booking in detail. |
| 15 | POST | `/api/v1/bookings/<uuid:pk>/cancel/` | `pk` = Booking UUID | Success envelope with updated booking detail and `status: "CANCELLED"` | Cancel an eligible booking and release the slot back to available. |
| 16 | POST | `/api/v1/payments/process/` | JSON body: `booking_id`, `result` | Success envelope with `booking_status`, `payment_status`, `availability_status` | Process a payment by calling the configured mock gateway over HTTP with Python `requests`. |
| 17 | POST | `/api/v1/payments/webhook/` | JSON body: `booking_id`, `result`, optional `gateway_reference` | Success envelope with final payment and booking state | Accept the same normalized webhook-style payload a real gateway would send. |
| 18 | POST | `/mock-payment-gateway/payments/` | JSON body: `payment_id`, `booking_id`, `amount`, `currency`, `result` | Success envelope with gateway `result` and `gateway_reference`; failed mock payments return HTTP `400` | Mock external payment service used by the payment client. |

### Important response format

All API responses use a consistent envelope:

```json
{
  "success": true,
  "message": "Booking created successfully.",
  "data": {}
}
```

Errors use the matching shape:

```json
{
  "success": false,
  "message": "This slot is no longer available.",
  "errors": {
    "availability_id": "This slot is no longer available."
  }
}
```

Every response also includes an `X-Request-ID` header, which is generated by the middleware if the client does not send one.

There is no auth-protected API in the current scope. The mock profiles are selected by ID.

---

# 21. API Request / Response Examples

## LSA Search

Request:

```http
GET /api/v1/lsas/search/?skill=autism&rating=4.5
```

Response:

```json
{
  "success": true,
  "message": "LSAs retrieved successfully.",
  "data": [
    {
      "id": "<uuid>",
      "name": "Alice",
      "rating": 4.8,
      "experience": 8,
      "hourly_rate": 60.0,
      "skills": ["Autism", "Speech Therapy"]
    }
  ]
}
```

## Create Booking

Request:

```http
POST /api/v1/bookings/
Content-Type: application/json
```

```json
{
  "parent_id": "<parent-uuid>",
  "availability_id": "<availability-uuid>"
}
```

Response:

```json
{
  "success": true,
  "message": "Booking created successfully.",
  "data": {
    "booking_id": "<booking-uuid>",
    "status": "PAYMENT_PENDING",
    "payment_status": "INITIATED",
    "availability_id": "<availability-uuid>"
  }
}
```

## Process Payment

Request:

```http
POST /api/v1/payments/process/
```

```json
{
  "booking_id": "<booking-uuid>",
  "result": "success",
  "gateway_reference": "gateway-123"
}
```

Response:

```json
{
  "success": true,
  "message": "Payment processed successfully.",
  "data": {
    "booking_id": "<booking-uuid>",
    "payment_id": "<payment-uuid>",
    "booking_status": "CONFIRMED",
    "payment_status": "SUCCESS",
    "availability_status": "BOOKED"
  }
}
```

## Payment Webhook

This is the same normalized payload a real gateway would send.

```http
POST /api/v1/payments/webhook/
```

```json
{
  "booking_id": "<booking-uuid>",
  "result": "success",
  "gateway_reference": "gateway-123"
}
```

## Parent Dashboard

```http
GET /api/v1/parents/<uuid:pk>/dashboard/
```

```json
{
  "success": true,
  "message": "Parent dashboard retrieved successfully.",
  "data": {
    "total_bookings": 3,
    "upcoming": 1,
    "completed": 1,
    "cancelled": 1,
    "failed": 0
  }
}
```

---

# 22. HTTP Status Codes

The relevant status codes in the project are:

- `200 OK` — normal GET and successful process actions
- `201 Created` — successful booking creation
- `400 Bad Request` — validation failure or unavailable slot
- `404 Not Found` — parent/booking/availability missing
- `503 Service Unavailable` — health check cannot reach the database
- `500 Internal Server Error` — unexpected exception handled by custom exception handler

Examples:

- Trying to book an already booked slot returns `400`.
- Passing a missing parent ID or booking ID returns `404`.
- Health check database failure returns `503`.
- The custom exception handler maps unexpected exceptions to a consistent error envelope with `500`.

This matches the quality checks in the project: API validation and error handling are not just generic; they are tied to actual business logic.

---

# 23. Validation

Validation exists at several layers.

## Serializer validation

Examples:

- `UUIDField` for IDs
- `ChoiceField` for payment result values (`success` or `failed`)
- date formats for `available_date`
- min/max values for rating and hourly rate
- non-empty strings for `skill`

## Service validation

Examples:

- parent must exist
- availability must exist
- slot must be in the future
- slot must be `AVAILABLE`
- duplicate booking on the same slot is rejected
- invalid booking cancellation state is rejected

## Database validation

Examples:

- `start_time < end_time`
- `rating 0..5`
- unique `LSASkill` combination
- unique `Booking.availability`
- PostgreSQL overlap guard for LSA availability times

This combination of validation is important because front-end validation alone is not enough for a backend homework project.

---

# 24. Exception Handling

The project uses a custom exception handler in `apps.common.exceptions`.

The handler does the following:

- converts `Http404` to DRF `NotFound`
- converts Django `PermissionDenied` to DRF `PermissionDenied`
- uses DRF’s default exception handling for validation errors
- catches unexpected exceptions and returns a consistent error payload
- logs unexpected exceptions with the request ID

The response envelope from `apps.common.responses` gives all errors a consistent structure:

```json
{
  "success": false,
  "message": "This slot is no longer available.",
  "errors": {
    "availability_id": "This slot is no longer available."
  }
}
```

This is one of the practical backend quality points the project demonstrates.

---

# 25. API Response Format

The API uses a simple consistent enveloped format.

Success:

```json
{
  "success": true,
  "message": "Booking created successfully.",
  "data": {
    "booking_id": "<uuid>",
    "status": "PAYMENT_PENDING",
    "payment_status": "INITIATED"
  }
}
```

Error:

```json
{
  "success": false,
  "message": "Booking not found.",
  "errors": {
    "detail": "Booking not found."
  }
}
```

The custom response helpers in `apps.common.responses` ensure that success and failure are shaped the same way across endpoints.

---

# 26. Logging

The repository has structured logging configured in `config.settings.base`.

Important details:

- log level defaults to `INFO`
- logs go to the console
- `RequestIDFilter` adds `request_id` to each log record
- `RequestIDMiddleware` reads or creates `X-Request-ID`
- app-specific loggers exist for:
  - `apps.bookings`
  - `apps.common`
  - `apps.lsas`
  - `apps.payments`

This makes it easier to debug API issues without leaking secret values.

The health check logs database probe failures with `logger.exception(...)` when the DB is not available.

---

# 27. Health Check

The actual health endpoints are defined in `config/urls.py`.

- `GET /health/live/` returns `{"status": "ok"}`
- `GET /health/ready/` runs `SELECT 1` and returns DB connection state
- `GET /health/` is a readiness alias used by Docker health checks

Example response:

```json
{
  "success": true,
  "message": "Application is ready.",
  "data": {
    "status": "ok",
    "database": "connected"
  }
}
```

If the database is not reachable, the app returns `503` and an error payload like:

```json
{
  "success": false,
  "message": "Application is not ready.",
  "errors": {
    "database": "unavailable"
  }
}
```

---

# 28. Docker Architecture

The repository uses Docker Compose with a single service named `backend`.

`docker-compose.yml` defines:

- service: `backend`
- build context: project root
- Dockerfile: `docker/backend/Dockerfile`
- env file: `.env`
- port mapping: `8000:8000`
- volume mounts for `backend/` and `tests/`
- health check hitting `http://127.0.0.1:8000/health/`
- network: `habot-network`

It does not spin up a separate local PostgreSQL container. The app expects a database via `DATABASE_URL`, which is consistent with the Neon/PostgreSQL design.

---

# 29. Docker Setup

Use these commands from the repo root:

```bash
git clone <repository-url>
cd habot-backend
cp .env.example .env
# fill in your SECRET_KEY and DATABASE_URL

docker compose up --build
```

The app then runs on:

```text
http://localhost:8000
```

Swagger UI is available at:

```text
http://localhost:8000/api/docs/
```

OpenAPI schema is available at:

```text
http://localhost:8000/api/schema/
```

The application also exposes Django Admin at:

```text
http://localhost:8000/admin/
```

---

# 30. Environment Variables

These are the actual environment variables used by the settings and sample config.

| Variable | Purpose | Required |
| --- | --- | --- |
| `DEBUG` | Enable or disable Django debug mode | Yes |
| `SECRET_KEY` | Django secret key | Yes |
| `ALLOWED_HOSTS` | Allowed host list | Yes |
| `DATABASE_URL` | PostgreSQL / Neon connection string | Yes |
| `CORS_ALLOW_ALL_ORIGINS` | Enables permissive CORS for dev/testing | Yes in sample `.env` |
| `PAYMENT_GATEWAY_URL` | Base URL for the mock HTTP payment gateway | Optional, defaults to `http://127.0.0.1:8000/mock-payment-gateway` |
| `PAYMENT_GATEWAY_TIMEOUT` | Timeout in seconds for the external payment HTTP request | Optional, defaults to `5.0` |
| `DJANGO_LOG_LEVEL` | Logger verbosity override | Optional |
| `SECURE_SSL_REDIRECT` | Production SSL redirect toggle | Optional production-only |
| `SECURE_HSTS_SECONDS` | HSTS duration | Optional production-only |
| `SESSION_COOKIE_SECURE` | Secure session cookie | Optional production-only |
| `CSRF_COOKIE_SECURE` | Secure CSRF cookie | Optional production-only |

The sample file `.env.example` includes the main values that are expected by local Docker setup.

---

# 31. Django Admin Setup

The project expects mock data to be created in Django Admin, not through a registration API.

Steps:

```bash
docker compose exec backend python manage.py migrate

docker compose exec backend python manage.py createsuperuser
```

Then open:

```text
http://localhost:8000/admin/
```

The recommended creation order is:

1. Create Parent
2. Create LSA
3. Create Skills
4. Assign Skills to LSA
5. Create Availability slots

This matches the intended business flow and keeps the project inside its hiring scope.

---

# 32. Running the Application

A new developer can follow this flow:

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill `SECRET_KEY` and `DATABASE_URL`.
3. Run:
   ```bash
   docker compose up --build
   ```
4. Run migrations if needed:
   ```bash
   docker compose exec backend python manage.py migrate
   ```
5. Create an admin user:
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```
6. Open `/admin/` and create mock Parent / LSA / Skill / Availability data.
7. Use Swagger at `/api/docs/` to test endpoints.
8. Call the main APIs from Postman or cURL.
9. Run the test suite:
   ```bash
   docker compose exec backend pytest
   ```

The project does not ship a frontend. The backend is designed to be used by Postman, Swagger, or a separate frontend app later.

---

# 33. Testing

The current verified test command is:

```bash
docker compose exec backend pytest
```

Current verification result:

```text
35 passed in 8.52s
```

This is the fresh result from the repo and should be treated as the current project verification state.

The tests cover:

- API contract consistency
- parent list/detail behavior
- LSA search and filter behavior
- slot availability logic
- booking creation and duplicate-booking protection
- payment success and failure flow
- `requests`-based mock gateway success, failure, timeout, connection failure, HTTP error, and explicit timeout behavior
- webhook idempotency
- parent dashboard and booking status history
- cancellation behavior
- database constraints and OpenAPI exposure
- query count optimization
- health checks

---

# 34. Test Suite Structure

| Test file | Purpose |
| --- | --- |
| `tests/test_api_contract.py` | Ensures global response envelopes and request ID headers |
| `tests/test_bookings.py` | Booking creation, duplicate protection, invalid parent/slot handling |
| `tests/test_payment_lifecycle.py` | Payment success/failure, webhook flow, idempotency |
| `tests/test_sprint2_apis.py` | Parent and LSA API behaviors, filters, validation |
| `tests/test_sprint5_dashboard.py` | Booking history, cancellation, dashboard summary |
| `tests/test_sprint6_hardening.py` | Query optimization, DB constraints, schema exposure, invalid date handling |
| `tests/test_health.py` | Health endpoints and DB readiness behavior |

---

# 35. Postman Testing

The APIs were manually tested in Postman for the end-to-end flow.

The recommended testing flow is:

```text
Health
  |
  v
Parent list/detail
  |
  v
LSA search
  |
  v
LSA detail
  |
  v
Availability listing
  |
  v
Create booking
  |
  v
Payment process / webhook
  |
  v
Booking status
  |
  v
Parent dashboard
  |
  v
Booking cancellation
```

There is no Postman collection checked in to the repository, so I am not claiming that one exists.

---

# 36. CI/CD

The project includes GitHub Actions in `.github/workflows/tests.yml`.

The workflow does the following:

- triggers on `push` and `pull_request`
- uses `ubuntu-latest`
- creates a `.env` file for the CI job
- builds the Docker backend image
- runs Django migrations in the container
- runs `pytest`

It does not include a deployment workflow. This is a test automation workflow, not a deployment pipeline.

---

# 37. API Documentation / Swagger

The project exposes OpenAPI and Swagger endpoints.

- Swagger UI: `http://localhost:8000/api/docs/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

The schema is generated through drf-spectacular and it includes the booking, payment, parent, and LSA endpoints.

This is useful for a developer to inspect request and response structures without reading code first.

---

# 38. Development Commands

Useful commands:

```bash
# Start application
docker compose up --build

# Stop application
docker compose down

# Rebuild image
docker compose build --no-cache backend

# View logs
docker compose logs -f backend

# Run migrations
docker compose exec backend python manage.py migrate

# Create admin
docker compose exec backend python manage.py createsuperuser

# Run tests
docker compose exec backend pytest

# Open Django shell
docker compose exec backend python manage.py shell
```

These are the commands that match the actual Docker configuration in this repo.

---

# 39. Technical Design Decisions

### Why PostgreSQL?

Because the project has several related entities and several transaction-sensitive operations. PostgreSQL handles that much better than a lightweight local DB, especially for booking locking and consistency checks.

### Why Neon?

Because the project is meant to be close to a production setup, and Neon gives us managed PostgreSQL without much friction. This is useful for a backend assessment because it demonstrates real-world database usage instead of an in-memory-only solution.

### Why Docker?

Because the repo is meant to be easy to run on any machine. The project uses a single backend service and standard Docker environment variables. That reduces local setup issues and makes the test workflow simpler.

### Why Django REST Framework?

Because the core requirement is JSON API creation, validation, and status handling. DRF gave the project a natural place for serializers, API views, and schema generation.

### Why a service layer?

Because the project needed business rules separated from the HTTP layer. The booking logic and payment logic are not placed directly inside views; they live in `services.py` so they can be tested and reused cleanly.

### Why database locking?

Because double booking is a real risk when two requests hit the same availability slot at the same time. `select_for_update()` and `transaction.atomic()` are not optional here; they are the actual protection used in the code.

### Why indexes?

Because the app performs frequent filters on LSA, date, status, and availability. I added the indexes that matter to the actual read patterns, especially around search and availability lookup.

### Why normalized tables?

Because the project includes reusable concept like skills, repeated parent data, and slot-specific bookings. Normalization keeps the data clean and avoids duplicates.

### Why mock users?

Because the assignment intentionally does not require full auth or registration. It focuses on the booking and payment flow, so mock Parent and LSA profiles are created through Django Admin.

### Why a mock HTTP payment gateway?

Because the project is a hiring assessment. The goal is to show external-service integration with Python `requests`, payment status handling, webhook processing, and idempotency without integrating a real billing system.

---

# 40. Security Considerations

The project has basic security settings but it is still a hiring-project backend, not a full production security setup.

Actual settings in the project include:

- `DEBUG` setting from environment variables
- `SECRET_KEY` from environment
- `ALLOWED_HOSTS`
- `CORS_ALLOW_ALL_ORIGINS` toggle
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` in production settings
- `X_FRAME_OPTIONS = "DENY"`
- `SECURE_REFERRER_POLICY = "same-origin"`

The project does not implement authentication or authorization for Parent/LSA users. That is intentional for the scope of this assignment.

There is no real secret leakage in the README; the sample environment values use placeholders rather than actual credentials.

---

# 41. What Is Intentionally Not Included

This project does not include:

- Parent/LSA authentication
- user registration flow
- JWT or OAuth
- real payment gateway integration
- email or SMS notifications
- Redis or Celery background jobs
- frontend application
- advanced monitoring stack
- caching layer

These are outside the hiring-project scope. That is not a weakness of the project; it keeps the work focused on the required backend behavior.

---

# 42. Future Improvements

If this project were extended later, the logical next steps would be:

- add authentication and authorization
- integrate with a real payment gateway
- add notification jobs for booking updates
- add Redis caching for search results
- add Celery for async work
- improve advanced search and filtering
- add monitoring and logs to a centralized platform
- add a frontend or admin dashboard

These are sensible improvements, but they are not part of the current project scope.

---

# 43. Project Verification Summary

```text
Backend: Django + DRF
Database: PostgreSQL / Neon-ready
Containerization: Docker
API Documentation: OpenAPI / Swagger
Testing: pytest
Automated Tests: 35 passed
Manual API Testing: Postman workflow completed
CI: GitHub Actions
```

This reflects the current repo state after verification.

---

# 44. Submission Checklist

- [x] Django backend implemented
- [x] PostgreSQL database
- [x] REST APIs
- [x] LSA search
- [x] Booking
- [x] Payment simulation
- [x] Webhook
- [x] N+1 optimization
- [x] Concurrency protection
- [x] Automated tests
- [x] Docker
- [x] Swagger/OpenAPI
- [x] GitHub Actions
- [x] Technical README

---

# 45. Final Developer Note

The main thing I focused on in this project was not just making the APIs work, but making sure the booking flow behaves correctly under real-world conditions. The database has to protect against duplicate bookings, the queries have to stay efficient, and the API has to return clear and consistent error states. I also kept the scope tight instead of adding auth or unrelated infrastructure because the hiring assignment was about the actual booking, search, and payment logic.

That is the core of this project, and it is what I wanted the backend to demonstrate clearly.

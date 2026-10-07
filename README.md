# Bulk Certificate Generator API

A production-style FastAPI backend for the Aereo Software Development Engineer assignment. It accepts a single request containing many recipients, validates the input, creates one certificate per valid recipient, tracks progress in a relational database, isolates individual failures, and exposes generated PDFs for download.

## Tech stack

- Python
- FastAPI
- SQLite + SQLAlchemy
- ReportLab for PDF generation
- Pytest + FastAPI TestClient

## Design

The API creates a **generation job** and individual **certificate records** in SQLite. Certificate generation is then started as a FastAPI `BackgroundTasks` job. Each recipient is processed independently and the database is updated after each certificate.

This design was chosen because:

1. The client makes one API request for the entire batch.
2. The API responds with a job ID instead of making the client wait for every PDF.
3. Progress can be tracked using successful + failed counts.
4. One certificate failure is caught and recorded without stopping the remaining recipients.
5. SQLite keeps the assignment easy to run locally while still demonstrating relational data modeling.
6. A production deployment could replace SQLite/background tasks with PostgreSQL + a durable queue such as Celery/RQ without changing the public API design.

## Setup

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Open Swagger UI at:

`http://127.0.0.1:8000/docs`

Health check:

`GET /health`

## Create a generation job

`POST /jobs`

Example JSON:

```json
{
  "event_name": "Python Bootcamp",
  "event_date": "2026-10-07",
  "completion_date": "2026-10-07",
  "issuer_name": "Aereo Demo",
  "recipients": [
    {
      "name": "Sneha Uppar",
      "email": "sneha@example.com"
    },
    {
      "name": "Rahul Sharma",
      "email": "rahul@example.com"
    }
  ]
}
```

The response contains the job ID, status, progress and per-recipient results.

## Check progress

`GET /jobs/{job_id}`

A job can have these states:

- `pending`
- `running`
- `completed`
- `completed_with_errors`

Each certificate has `pending`, `success` or `failed` status.

## Retrieve certificates

List results:

`GET /jobs/{job_id}/certificates`

Download an individual generated PDF:

`GET /certificates/{certificate_id}/download`

## Validation and failure handling

Pydantic validates recipient names, email addresses, dates, and batch size. Invalid requests return HTTP 422.

During processing, certificate generation is wrapped per recipient. If one PDF fails, its error is stored and the next recipient is processed. A job with at least one failure ends as `completed_with_errors`.

## Tests

Run:

```bash
python -m pytest -q
```

The test suite covers:

- Creating a generation job
- Input validation
- PDF certificate generation
- Job status/progress
- Individual certificate failure isolation
- Certificate retrieval/download

## Project structure

```text
.
.
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── services/
│       ├── certificate_service.py
│       └── job_service.py
├── tests/
│   └── test_api.py
├── storage/              # Generated PDFs/runtime files
├── requirements.txt
├── .gitignore
└── README.md
```

## Possible interview discussion points

### Why FastAPI?
FastAPI provides typed request validation with Pydantic, automatic OpenAPI/Swagger documentation, and a small amount of code for REST APIs.

### Why a relational database?
Jobs and certificates have a clear one-to-many relationship. A relational schema makes it straightforward to query job progress and individual certificate status.

### Why background processing?
Bulk PDF generation can take time. Returning a job ID quickly keeps the API responsive and gives the client a way to poll progress.

### What would change in production?
Use PostgreSQL for durable storage, object storage such as S3 for PDFs, and a durable task queue such as Celery/RQ. Add authentication, rate limiting, structured logging and observability.

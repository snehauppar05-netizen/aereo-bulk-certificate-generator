from datetime import date

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.services import certificate_service


client = TestClient(app)


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_create_generation_job():
    reset_db()
    response = client.post(
        "/jobs",
        json={
            "certificate_title": "Certificate of Completion",
            "event_name": "Python Bootcamp",
            "completion_date": str(date.today()),
            "issuer_name": "Aereo Demo",
            "recipients": [{"name": "Sneha Uppar", "email": "sneha@example.com"}],
        },
    )
    assert response.status_code == 202
    body = response.json()
    assert body["total"] == 1
    assert body["status"] == "pending"

    completed = client.get(f"/jobs/{body["id"]}").json()
    assert completed["successful"] == 1
    assert completed["status"] == "completed"
    assert completed["certificates"][0]["status"] == "success"


def test_input_validation():
    reset_db()
    response = client.post(
        "/jobs",
        json={
            "event_name": "Python Bootcamp",
            "completion_date": "2026-10-07",
            "issuer_name": "Aereo Demo",
            "recipients": [{"name": "A", "email": "not-an-email"}],
        },
    )
    assert response.status_code == 422


def test_certificate_generation_and_retrieval():
    reset_db()
    response = client.post(
        "/jobs",
        json={
            "event_name": "Python Bootcamp",
            "completion_date": "2026-10-07",
            "issuer_name": "Aereo Demo",
            "recipients": [{"name": "Test User"}],
        },
    )
    certificate_id = response.json()["certificates"][0]["id"]
    download = client.get(f"/certificates/{certificate_id}/download")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"


def test_job_status_progress():
    reset_db()
    response = client.post(
        "/jobs",
        json={
            "event_name": "Python Bootcamp",
            "completion_date": "2026-10-07",
            "issuer_name": "Aereo Demo",
            "recipients": [{"name": "One User"}, {"name": "Two User"}],
        },
    )
    job_id = response.json()["id"]
    status = client.get(f"/jobs/{job_id}")
    body = status.json()
    assert body["progress_percent"] == 100.0
    assert body["total"] == 2
    assert body["successful"] == 2


def test_individual_certificate_failure_does_not_stop_batch(monkeypatch):
    reset_db()
    original = certificate_service.generate_certificate
    calls = {"count": 0}

    def flaky_generator(**kwargs):
        calls["count"] += 1
        if kwargs["recipient_name"] == "Bad User":
            raise RuntimeError("Simulated PDF generation failure")
        return original(**kwargs)

    monkeypatch.setattr("app.services.job_service.generate_certificate", flaky_generator)

    response = client.post(
        "/jobs",
        json={
            "event_name": "Python Bootcamp",
            "completion_date": "2026-10-07",
            "issuer_name": "Aereo Demo",
            "recipients": [
                {"name": "Good User"},
                {"name": "Bad User"},
                {"name": "Another Good User"},
            ],
        },
    )
    body = response.json()
    assert calls["count"] == 3
    body = client.get(f"/jobs/{body["id"]}").json()
    assert body["status"] == "completed_with_errors"
    assert body["successful"] == 2
    assert body["failed"] == 1
    statuses = {item["recipient_name"]: item["status"] for item in body["certificates"]}
    assert statuses["Good User"] == "success"
    assert statuses["Bad User"] == "failed"
    assert statuses["Another Good User"] == "success"

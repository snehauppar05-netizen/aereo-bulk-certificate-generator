from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Certificate, GenerationJob
from .schemas import GenerationJobCreate, JobResponse
from .services.job_service import process_job

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator API",
    version="1.0.0",
    description="Bulk certificate generation service built for the Aereo engineering assignment.",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/jobs", response_model=JobResponse, status_code=202)
def create_generation_job(
    payload: GenerationJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = GenerationJob(
        certificate_title=payload.certificate_title,
        event_name=payload.event_name,
        completion_date=payload.completion_date,
        issuer_name=payload.issuer_name,
        status="pending",
        total=len(payload.recipients),
        successful=0,
        failed=0,
    )
    db.add(job)
    db.flush()

    for recipient in payload.recipients:
        db.add(
            Certificate(
                job_id=job.id,
                recipient_name=recipient.name,
                recipient_email=str(recipient.email) if recipient.email else None,
                status="pending",
            )
        )

    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_job, job.id)

    return build_job_response(job, db)


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return build_job_response(job, db)


@app.get("/jobs/{job_id}/certificates", response_model=JobResponse)
def list_job_certificates(job_id: int, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return build_job_response(job, db)


@app.get("/certificates/{certificate_id}/download")
def download_certificate(certificate_id: int, db: Session = Depends(get_db)):
    certificate = db.get(Certificate, certificate_id)
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if certificate.status != "success" or not certificate.file_path:
        raise HTTPException(status_code=409, detail="Certificate is not available")

    path = Path(certificate.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Certificate file is missing")

    return FileResponse(path, media_type="application/pdf", filename=path.name)


def build_job_response(job: GenerationJob, db: Session) -> JobResponse:
    certificates = (
        db.query(Certificate)
        .filter(Certificate.job_id == job.id)
        .order_by(Certificate.id)
        .all()
    )
    processed = job.successful + job.failed
    progress = round((processed / job.total) * 100, 2) if job.total else 100.0

    return JobResponse(
        id=job.id,
        status=job.status,
        total=job.total,
        successful=job.successful,
        failed=job.failed,
        progress_percent=progress,
        certificates=[
            {
                "id": item.id,
                "recipient_name": item.recipient_name,
                "recipient_email": item.recipient_email,
                "status": item.status,
                "error_message": item.error_message,
                "download_url": f"/certificates/{item.id}/download" if item.status == "success" else None,
            }
            for item in certificates
        ],
    )

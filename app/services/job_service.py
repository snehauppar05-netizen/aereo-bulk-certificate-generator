from pathlib import Path

from sqlalchemy.orm import Session

from ..models import Certificate, GenerationJob
from .certificate_service import certificate_file_path, generate_certificate


def process_job(job_id: int) -> None:
    """Process each recipient independently so one failure does not stop the batch."""
    from ..database import SessionLocal

    db: Session = SessionLocal()
    try:
        job = db.get(GenerationJob, job_id)
        if not job:
            return

        job.status = "running"
        db.commit()

        certificates = (
            db.query(Certificate)
            .filter(Certificate.job_id == job_id)
            .order_by(Certificate.id)
            .all()
        )

        for certificate in certificates:
            try:
                output_path = certificate_file_path(job_id, certificate.id)
                generate_certificate(
                    output_path=output_path,
                    recipient_name=certificate.recipient_name,
                    certificate_title=job.certificate_title,
                    event_name=job.event_name,
                    completion_date=job.completion_date.isoformat(),
                    issuer_name=job.issuer_name,
                )
                certificate.status = "success"
                certificate.file_path = str(output_path)
                certificate.error_message = None
                job.successful += 1
            except Exception as exc:  # one bad certificate must not stop the job
                certificate.status = "failed"
                certificate.error_message = str(exc)
                job.failed += 1

            db.commit()

        job.status = "completed_with_errors" if job.failed else "completed"
        db.commit()
    finally:
        db.close()

from pathlib import Path
from uuid import uuid4

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage"


def generate_certificate(
    *,
    output_path: Path,
    recipient_name: str,
    certificate_title: str,
    event_name: str,
    completion_date: str,
    issuer_name: str,
) -> None:
    """Generate one certificate using the application's single predefined template."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))

    # Fixed certificate template: border, heading, recipient, event, date and issuer.
    margin = 12 * mm
    pdf.setLineWidth(3)
    pdf.rect(margin, margin, page_width - 2 * margin, page_height - 2 * margin)
    pdf.setLineWidth(1)
    pdf.rect(margin + 5 * mm, margin + 5 * mm, page_width - 2 * (margin + 5 * mm), page_height - 2 * (margin + 5 * mm))

    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(page_width / 2, page_height - 55 * mm, certificate_title)

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(page_width / 2, page_height - 72 * mm, "This certificate is proudly presented to")

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(page_width / 2, page_height - 95 * mm, recipient_name)

    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(page_width / 2, page_height - 115 * mm, f"for successfully completing {event_name}")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(35 * mm, 35 * mm, f"Date: {completion_date}")
    pdf.drawRightString(page_width - 35 * mm, 35 * mm, f"Issued by: {issuer_name}")

    pdf.save()


def certificate_file_path(job_id: int, certificate_id: int) -> Path:
    return STORAGE_DIR / str(job_id) / f"certificate_{certificate_id}_{uuid4().hex[:8]}.pdf"

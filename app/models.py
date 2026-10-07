from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    certificate_title: Mapped[str] = mapped_column(String(150))
    event_name: Mapped[str] = mapped_column(String(200))
    completion_date: Mapped[date] = mapped_column(Date)
    issuer_name: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    total: Mapped[int] = mapped_column(Integer, default=0)
    successful: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    certificates = relationship(
        "Certificate", back_populates="job", cascade="all, delete-orphan"
    )


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("generation_jobs.id"))
    recipient_name: Mapped[str] = mapped_column(String(100))
    recipient_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("GenerationJob", back_populates="certificates")

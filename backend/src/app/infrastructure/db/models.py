from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.domain.enums import DownloadJobStatus
from app.infrastructure.db.base import Base


class DownloadJobModel(Base):
    __tablename__ = "download_jobs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    status: Mapped[DownloadJobStatus] = mapped_column(
        Enum(DownloadJobStatus, name="download_job_status", native_enum=False),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    names_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    downloaded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_known: Mapped[int | None] = mapped_column(Integer, nullable=True)

    files: Mapped[list["DownloadedFileModel"]] = relationship(back_populates="job")


class DownloadedFileModel(Base):
    __tablename__ = "downloaded_files"
    __table_args__ = (UniqueConstraint("filename", name="uq_downloaded_files_filename"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    job_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("download_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    job: Mapped[DownloadJobModel | None] = relationship(back_populates="files")
    digit_stats: Mapped["DigitStatsCacheModel | None"] = relationship(
        back_populates="file",
        uselist=False,
    )


class DigitStatsCacheModel(Base):
    __tablename__ = "digit_stats_cache"

    file_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("downloaded_files.id", ondelete="CASCADE"),
        primary_key=True,
    )
    counts: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    file: Mapped[DownloadedFileModel] = relationship(back_populates="digit_stats")

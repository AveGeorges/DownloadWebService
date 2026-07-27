"""Initial schema: download jobs, files, digit stats cache.

Revision ID: 001_initial
Revises:
Create Date: 2026-07-27 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "download_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "waiting",
                "completed",
                "failed",
                name="download_job_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("names_received", sa.Integer(), nullable=False),
        sa.Column("downloaded_count", sa.Integer(), nullable=False),
        sa.Column("total_known", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_download_jobs_status", "download_jobs", ["status"])

    op.create_table(
        "downloaded_files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_path", sa.String(length=1024), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["download_jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("filename", name="uq_downloaded_files_filename"),
    )
    op.create_index("ix_downloaded_files_job_id", "downloaded_files", ["job_id"])
    op.create_index("ix_downloaded_files_downloaded_at", "downloaded_files", ["downloaded_at"])

    op.create_table(
        "digit_stats_cache",
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("counts", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["downloaded_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("file_id"),
    )


def downgrade() -> None:
    op.drop_table("digit_stats_cache")
    op.drop_index("ix_downloaded_files_downloaded_at", table_name="downloaded_files")
    op.drop_index("ix_downloaded_files_job_id", table_name="downloaded_files")
    op.drop_table("downloaded_files")
    op.drop_index("ix_download_jobs_status", table_name="download_jobs")
    op.drop_table("download_jobs")

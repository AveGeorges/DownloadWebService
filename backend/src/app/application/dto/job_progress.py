from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class JobProgressView:
    job_id: str
    status: str
    names_received: int
    downloaded_count: int
    started_at: str | None = None
    error: str | None = None

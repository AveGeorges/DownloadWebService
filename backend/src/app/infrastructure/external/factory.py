from app.config import Settings, get_settings
from app.infrastructure.external.catalog_client import ExternalCatalogClient


def build_external_catalog_client(
    settings: Settings | None = None,
) -> ExternalCatalogClient:
    cfg = settings or get_settings()
    return ExternalCatalogClient(
        base_url=cfg.external_api_base_url,
        candidate_id=cfg.x_candidate_id,
        timeout_seconds=cfg.external_api_timeout_seconds,
        max_attempts=cfg.external_api_max_attempts,
        min_interval_seconds=cfg.external_api_min_interval_seconds,
    )

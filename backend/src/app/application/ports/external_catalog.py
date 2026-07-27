from collections.abc import Sequence
from typing import Protocol


class ExternalCatalogPort(Protocol):
    """Port for the external file catalog API."""

    def list_names(self) -> list[str]:
        """Return file names not yet marked as downloaded (empty = catalog done)."""

    def download(self, names: Sequence[str]) -> bytes:
        """Download up to 3 files as a ZIP archive payload."""

    def mark_downloaded(self, names: Sequence[str]) -> None:
        """Acknowledge downloaded files so they leave the names feed."""

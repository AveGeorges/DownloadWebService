from __future__ import annotations

import io
import zipfile
from pathlib import PurePosixPath

from app.domain.exceptions import CatalogRequestError
from app.domain.filename import sanitize_filename


def extract_zip_files(zip_bytes: bytes) -> dict[str, bytes]:
    """Extract file members from a ZIP payload into ``{safe_filename: content}``."""
    if not zip_bytes:
        raise CatalogRequestError("Empty ZIP payload")

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            result: dict[str, bytes] = {}
            for info in archive.infolist():
                if info.is_dir():
                    continue
                raw_name = PurePosixPath(info.filename.replace("\\", "/")).name
                if not raw_name:
                    continue
                safe_name = sanitize_filename(raw_name)
                result[safe_name] = archive.read(info)
            return result
    except zipfile.BadZipFile as exc:
        raise CatalogRequestError("Invalid ZIP payload from catalog API") from exc

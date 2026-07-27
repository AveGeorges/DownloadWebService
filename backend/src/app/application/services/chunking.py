from collections.abc import Iterator, Sequence

MAX_DOWNLOAD_BATCH = 3


def chunked[T](items: Sequence[T], size: int = MAX_DOWNLOAD_BATCH) -> Iterator[list[T]]:
    """Yield successive chunks of at most ``size`` items."""
    if size < 1:
        raise ValueError("chunk size must be >= 1")
    for index in range(0, len(items), size):
        yield list(items[index : index + size])

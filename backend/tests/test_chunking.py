from app.application.services.chunking import chunked


def test_chunked_by_three() -> None:
    assert list(chunked(["a", "b", "c", "d", "e"], size=3)) == [
        ["a", "b", "c"],
        ["d", "e"],
    ]


def test_chunked_empty() -> None:
    assert list(chunked([], size=3)) == []

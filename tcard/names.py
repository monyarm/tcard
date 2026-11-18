"""Query text normalisation: `_` stands for a space, apostrophes are ignored."""

from __future__ import annotations

_APOSTROPHES = str.maketrans("", "", "'\u2018\u2019\u02bc`")


def normalize(text: str) -> str:
    folded = text.replace("_", " ").translate(_APOSTROPHES).casefold()
    return " ".join(folded.split())


def split_path(query: str) -> list[str]:
    return [part for part in (normalize(chunk) for chunk in query.split(":")) if part]

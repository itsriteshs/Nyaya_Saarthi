"""Nondestructive classification normalization. Span extraction uses the original input."""
import re
import unicodedata


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def text_template(text: str) -> str:
    """Conservative near-duplicate key: ignore numerical substitutions only."""
    return re.sub(r"\d+", "#", normalize_text(text))

import re
import unicodedata


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_regex(pattern: str) -> str:
    return normalize_text(pattern)
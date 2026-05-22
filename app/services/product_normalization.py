import re
import unicodedata


def _katakana_to_hiragana(value: str) -> str:
    chars: list[str] = []
    for char in value:
        codepoint = ord(char)
        if 0x30A1 <= codepoint <= 0x30F6:
            chars.append(chr(codepoint - 0x60))
        else:
            chars.append(char)
    return "".join(chars)


def normalize_product_key(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = re.sub(r"\s+", "", normalized)
    normalized = _katakana_to_hiragana(normalized)

    return normalized or None

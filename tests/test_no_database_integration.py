from pathlib import Path


OCR_API_BOUNDARY_FILES = sorted(Path("app").rglob("*.py"))

FORBIDDEN_DB_API_REFERENCES = [
    "database api",
    "db api",
    "database_api",
    "db_api",
    "accounting api",
    "accounting_api",
    "inventory api",
    "inventory_api",
]


def test_ocr_api_boundary_does_not_call_database_api() -> None:
    for path in OCR_API_BOUNDARY_FILES:
        source = path.read_text(encoding="utf-8").lower()

        for forbidden in FORBIDDEN_DB_API_REFERENCES:
            assert forbidden not in source, f"{path} references {forbidden!r}"

from datetime import datetime, date


def parse_yyyymmdd(value: int) -> date:
    value_text = str(value)
    if len(value_text) != 8 or not value_text.isdigit():
        raise ValueError("date must be a YYYYMMDD integer")
    return datetime.strptime(value_text, "%Y%m%d").date()


def format_yyyymmdd(value: date) -> int:
    return int(value.strftime("%Y%m%d"))

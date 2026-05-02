from datetime import datetime, date


def parse_yyyymmdd(value: int) -> date:
    return datetime.strptime(str(value), "%Y%m%d").date()


def format_yyyymmdd(value: date) -> int:
    return int(value.strftime("%Y%m%d"))
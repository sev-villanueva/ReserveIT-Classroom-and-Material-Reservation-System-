from datetime import date, datetime, time


def parse_date(text):
    try:
        return datetime.strptime((text or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_time(text):
    try:
        return datetime.strptime((text or "").strip(), "%H:%M").time()
    except ValueError:
        return None


def to_int(text):
    try:
        return int(str(text).strip())
    except (TypeError, ValueError):
        return None


def is_past(day: date, start: time):
    return datetime.combine(day, start) < datetime.now()

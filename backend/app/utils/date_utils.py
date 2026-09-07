from datetime import datetime, date, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Tuple

IST = ZoneInfo("Asia/Kolkata")

def get_now_ist() -> datetime:
    """Returns the current aware datetime in IST."""
    return datetime.now(IST)

def get_today_ist() -> date:
    """Returns the current date in IST."""
    return get_now_ist().date()

def get_current_week_bounds() -> Tuple[datetime, datetime]:
    """
    Returns (start, end) aware datetimes in IST for the current week.
    Week starts on Monday 00:00:00 and ends on Sunday 23:59:59.
    """
    now = get_now_ist()
    # weekday() returns 0 for Monday, 6 for Sunday
    days_since_monday = now.weekday()
    
    start_of_week = now.replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=days_since_monday)
    
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
    return start_of_week, end_of_week

def get_previous_week_bounds() -> Tuple[datetime, datetime]:
    """
    Returns (start, end) aware datetimes in IST for the previous week.
    """
    start_of_current, _ = get_current_week_bounds()
    start_of_previous = start_of_current - timedelta(days=7)
    end_of_previous = start_of_previous + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
    return start_of_previous, end_of_previous

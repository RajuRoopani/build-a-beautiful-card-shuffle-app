"""
datetime_utils.py — Date and time utilities module.
"""

from datetime import datetime, date, timedelta


def format_duration(seconds: int) -> str:
    """
    Convert seconds to a human-readable duration string.

    Converts a number of seconds into a formatted string with days, hours,
    minutes, and seconds. Once a higher unit appears, all lower units are
    shown (including zeros). Leading zero units are omitted.

    Args:
        seconds: The number of seconds to format (must be non-negative).

    Returns:
        A formatted duration string (e.g., '2h 30m 15s', '1d 0h 0m 0s').

    Raises:
        ValueError: If seconds is negative.

    Examples:
        >>> format_duration(0)
        '0s'
        >>> format_duration(45)
        '45s'
        >>> format_duration(150)
        '2m 30s'
        >>> format_duration(9015)
        '2h 30m 15s'
        >>> format_duration(86400)
        '1d 0h 0m 0s'
    """
    if seconds < 0:
        raise ValueError("seconds must be non-negative")

    if seconds == 0:
        return "0s"

    # Calculate time units
    days = seconds // 86400
    remainder = seconds % 86400

    hours = remainder // 3600
    remainder = remainder % 3600

    minutes = remainder // 60
    secs = remainder % 60

    # Build result based on the highest unit present
    parts = []

    if days > 0:
        parts.append(f"{days}d")
        parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
    elif hours > 0:
        parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
    elif minutes > 0:
        parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
    else:
        parts.append(f"{secs}s")

    return " ".join(parts)


def parse_date(text: str) -> datetime:
    """
    Parse various date string formats into a datetime object.

    Attempts to parse the input string against multiple common date formats:
    - ISO 8601: '2025-01-15'
    - ISO 8601 with time: '2025-01-15T10:30:00'
    - Abbreviated month: 'Jan 15 2025'
    - Full month with comma: 'January 15, 2025'
    - DD/MM/YYYY (European): '15/01/2025'

    Args:
        text: The date string to parse.

    Returns:
        A datetime object parsed from the input string.

    Raises:
        ValueError: If the string cannot be parsed in any recognized format.

    Examples:
        >>> parse_date('2025-01-15')
        datetime.datetime(2025, 1, 15, 0, 0)
        >>> parse_date('2025-01-15T10:30:00')
        datetime.datetime(2025, 1, 15, 10, 30)
        >>> parse_date('Jan 15 2025')
        datetime.datetime(2025, 1, 15, 0, 0)
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S",  # ISO 8601 with time
        "%Y-%m-%d",            # ISO 8601
        "%b %d %Y",            # Abbreviated month: Jan 15 2025
        "%B %d, %Y",           # Full month with comma: January 15, 2025
        "%d/%m/%Y",            # DD/MM/YYYY (European)
    ]

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: '{text}'")


def days_until(target: date) -> int:
    """
    Calculate the number of days from today to a target date.

    Args:
        target: The target date as a datetime.date object.

    Returns:
        The number of days until the target date. Positive if in the future,
        negative if in the past, zero if today.

    Examples:
        >>> days_until(date.today())
        0
        >>> days_until(date.today() + timedelta(days=5))
        5
    """
    today = date.today()
    delta = target - today
    return delta.days


def business_days_between(start: date, end: date) -> int:
    """
    Count weekdays (Monday-Friday) between two dates, inclusive.

    Counts all days from start to end (inclusive of both) that fall on
    Monday through Friday (weekdays).

    Args:
        start: The start date as a datetime.date object.
        end: The end date as a datetime.date object.

    Returns:
        The number of weekdays (Mon-Fri) between start and end, inclusive.

    Raises:
        ValueError: If start > end.

    Examples:
        >>> business_days_between(date(2025, 1, 6), date(2025, 1, 10))
        5
        >>> business_days_between(date(2025, 1, 11), date(2025, 1, 12))
        0
        >>> business_days_between(date(2025, 1, 13), date(2025, 1, 13))
        1
    """
    if start > end:
        raise ValueError("start date must be less than or equal to end date")

    count = 0
    current = start

    while current <= end:
        # weekday() returns 0-6 where 0=Monday, 6=Sunday
        if current.weekday() < 5:  # 0-4 are Mon-Fri
            count += 1
        current += timedelta(days=1)

    return count

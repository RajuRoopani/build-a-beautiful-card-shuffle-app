"""
test_datetime_utils.py — Unit tests for the date/time utilities module.

Run with:
    python -m pytest tests/test_datetime_utils.py -v
"""

import pytest
from datetime import datetime, date
from unittest.mock import patch

from src.datetime_utils.datetime_utils import (
    format_duration,
    parse_date,
    days_until,
    business_days_between,
)


# ---------------------------------------------------------------------------
# format_duration
# ---------------------------------------------------------------------------

class TestFormatDuration:
    """Test format_duration(seconds: int) -> str."""

    def test_zero_seconds(self) -> None:
        """Zero seconds returns '0s'."""
        assert format_duration(0) == "0s"

    def test_only_seconds(self) -> None:
        """45 seconds returns '45s'."""
        assert format_duration(45) == "45s"

    def test_minutes_and_seconds(self) -> None:
        """150 seconds returns '2m 30s'."""
        assert format_duration(150) == "2m 30s"

    def test_hours_minutes_seconds(self) -> None:
        """9015 seconds returns '2h 30m 15s'."""
        assert format_duration(9015) == "2h 30m 15s"

    def test_full_day_format(self) -> None:
        """86400 seconds (1 day) returns '1d 0h 0m 0s'."""
        assert format_duration(86400) == "1d 0h 0m 0s"

    def test_one_of_each_unit(self) -> None:
        """90061 seconds (1d 1h 1m 1s) returns '1d 1h 1m 1s'."""
        assert format_duration(90061) == "1d 1h 1m 1s"

    def test_hours_only_no_seconds(self) -> None:
        """3600 seconds (1 hour) returns '1h 0m 0s'."""
        assert format_duration(3600) == "1h 0m 0s"

    def test_negative_input_raises_value_error(self) -> None:
        """Negative input raises ValueError."""
        with pytest.raises(ValueError):
            format_duration(-1)


# ---------------------------------------------------------------------------
# parse_date
# ---------------------------------------------------------------------------

class TestParseDate:
    """Test parse_date(text: str) -> datetime."""

    def test_parse_iso_date_only(self) -> None:
        """ISO date format '2025-01-15' returns datetime(2025, 1, 15)."""
        result = parse_date("2025-01-15")
        assert result == datetime(2025, 1, 15)

    def test_parse_iso_datetime(self) -> None:
        """ISO datetime '2025-01-15T10:30:00' returns datetime(2025, 1, 15, 10, 30, 0)."""
        result = parse_date("2025-01-15T10:30:00")
        assert result == datetime(2025, 1, 15, 10, 30, 0)

    def test_parse_month_day_year_abbrev(self) -> None:
        """Abbreviated month 'Jan 15 2025' returns datetime(2025, 1, 15)."""
        result = parse_date("Jan 15 2025")
        assert result == datetime(2025, 1, 15)

    def test_parse_full_month_name(self) -> None:
        """Full month name 'January 15, 2025' returns datetime(2025, 1, 15)."""
        result = parse_date("January 15, 2025")
        assert result == datetime(2025, 1, 15)

    def test_parse_european_format(self) -> None:
        """European format '15/01/2025' returns datetime(2025, 1, 15)."""
        result = parse_date("15/01/2025")
        assert result == datetime(2025, 1, 15)

    def test_parse_invalid_date_raises_value_error(self) -> None:
        """Invalid date string 'not a date' raises ValueError."""
        with pytest.raises(ValueError):
            parse_date("not a date")


# ---------------------------------------------------------------------------
# days_until
# ---------------------------------------------------------------------------

class TestDaysUntil:
    """Test days_until(target: date) -> int with mocked date.today()."""

    @patch("src.datetime_utils.datetime_utils.date")
    def test_future_date(self, mock_date: object) -> None:
        """Days until future date returns positive integer."""
        # Set mock today to 2025-01-15, and allow date() constructor to work normally
        mock_date.today.return_value = date(2025, 1, 15)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        result = days_until(date(2025, 1, 20))
        assert result == 5

    @patch("src.datetime_utils.datetime_utils.date")
    def test_past_date(self, mock_date: object) -> None:
        """Days until past date returns negative integer."""
        mock_date.today.return_value = date(2025, 1, 15)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        result = days_until(date(2025, 1, 10))
        assert result == -5

    @patch("src.datetime_utils.datetime_utils.date")
    def test_same_date(self, mock_date: object) -> None:
        """Days until same date returns 0."""
        mock_date.today.return_value = date(2025, 1, 15)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        result = days_until(date(2025, 1, 15))
        assert result == 0


# ---------------------------------------------------------------------------
# business_days_between
# ---------------------------------------------------------------------------

class TestBusinessDaysBetween:
    """Test business_days_between(start: date, end: date) -> int."""

    def test_monday_to_friday_same_week(self) -> None:
        """Monday to Friday returns 5 business days."""
        # 2025-01-06 is Monday, 2025-01-10 is Friday
        result = business_days_between(date(2025, 1, 6), date(2025, 1, 10))
        assert result == 5

    def test_monday_to_sunday(self) -> None:
        """Monday to Sunday (next day after Friday) returns 5 business days."""
        # 2025-01-06 is Monday, 2025-01-12 is Sunday
        result = business_days_between(date(2025, 1, 6), date(2025, 1, 12))
        assert result == 5

    def test_saturday_to_sunday(self) -> None:
        """Saturday to Sunday returns 0 business days (both are weekends)."""
        # 2025-01-11 is Saturday, 2025-01-12 is Sunday
        result = business_days_between(date(2025, 1, 11), date(2025, 1, 12))
        assert result == 0

    def test_same_day_saturday(self) -> None:
        """Same day on Saturday returns 0 business days (weekend)."""
        # 2025-01-11 is Saturday
        result = business_days_between(date(2025, 1, 11), date(2025, 1, 11))
        assert result == 0

    def test_same_day_monday(self) -> None:
        """Same day on Monday returns 1 business day (weekday)."""
        # 2025-01-06 is Monday
        result = business_days_between(date(2025, 1, 6), date(2025, 1, 6))
        assert result == 1

    def test_start_after_end_raises_value_error(self) -> None:
        """Start date after end date raises ValueError."""
        with pytest.raises(ValueError):
            business_days_between(date(2025, 1, 10), date(2025, 1, 6))

"""
test_datetime_utils.py — Tests for the datetime_utils module.
"""

import pytest
from datetime import datetime, date, timedelta
from src.datetime_utils import format_duration, parse_date, days_until, business_days_between


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_zero_seconds(self):
        """Test formatting 0 seconds."""
        assert format_duration(0) == "0s"

    def test_only_seconds(self):
        """Test formatting seconds only."""
        assert format_duration(45) == "45s"

    def test_minutes_and_seconds(self):
        """Test formatting minutes and seconds."""
        assert format_duration(150) == "2m 30s"

    def test_hours_minutes_seconds(self):
        """Test formatting hours, minutes, and seconds."""
        assert format_duration(9015) == "2h 30m 15s"

    def test_days_with_zeros(self):
        """Test formatting with days shows all lower units."""
        assert format_duration(86400) == "1d 0h 0m 0s"

    def test_days_all_nonzero(self):
        """Test formatting days with all non-zero components."""
        assert format_duration(90061) == "1d 1h 1m 1s"

    def test_hours_only(self):
        """Test formatting with only hours set."""
        assert format_duration(3600) == "1h 0m 0s"

    def test_negative_seconds_raises_error(self):
        """Test that negative seconds raises ValueError."""
        with pytest.raises(ValueError):
            format_duration(-1)

    def test_large_duration(self):
        """Test formatting a large duration."""
        # 3 days + 5 hours + 20 minutes + 30 seconds
        seconds = 3 * 86400 + 5 * 3600 + 20 * 60 + 30
        assert format_duration(seconds) == "3d 5h 20m 30s"

    def test_one_second(self):
        """Test formatting 1 second."""
        assert format_duration(1) == "1s"


class TestParseDate:
    """Tests for parse_date function."""

    def test_iso_8601_date_only(self):
        """Test parsing ISO 8601 date format."""
        result = parse_date("2025-01-15")
        assert result == datetime(2025, 1, 15, 0, 0)

    def test_iso_8601_with_time(self):
        """Test parsing ISO 8601 with time."""
        result = parse_date("2025-01-15T10:30:00")
        assert result == datetime(2025, 1, 15, 10, 30, 0)

    def test_abbreviated_month(self):
        """Test parsing abbreviated month format."""
        result = parse_date("Jan 15 2025")
        assert result == datetime(2025, 1, 15, 0, 0)

    def test_full_month_with_comma(self):
        """Test parsing full month with comma."""
        result = parse_date("January 15, 2025")
        assert result == datetime(2025, 1, 15, 0, 0)

    def test_european_date_format(self):
        """Test parsing DD/MM/YYYY format."""
        result = parse_date("15/01/2025")
        assert result == datetime(2025, 1, 15, 0, 0)

    def test_unparseable_string_raises_error(self):
        """Test that unparseable string raises ValueError."""
        with pytest.raises(ValueError, match="Unable to parse date"):
            parse_date("not a date")

    def test_invalid_date_raises_error(self):
        """Test that invalid date raises ValueError."""
        with pytest.raises(ValueError, match="Unable to parse date"):
            parse_date("2025-13-45")  # Invalid month and day

    def test_multiple_months(self):
        """Test parsing different months."""
        assert parse_date("Feb 28 2025") == datetime(2025, 2, 28)
        assert parse_date("December 25, 2025") == datetime(2025, 12, 25)


class TestDaysUntil:
    """Tests for days_until function."""

    def test_today_returns_zero(self):
        """Test that today returns 0."""
        assert days_until(date.today()) == 0

    def test_future_date(self):
        """Test that future date returns positive integer."""
        future = date.today() + timedelta(days=5)
        assert days_until(future) == 5

    def test_past_date(self):
        """Test that past date returns negative integer."""
        past = date.today() - timedelta(days=5)
        assert days_until(past) == -5

    def test_tomorrow(self):
        """Test tomorrow is 1 day away."""
        tomorrow = date.today() + timedelta(days=1)
        assert days_until(tomorrow) == 1

    def test_yesterday(self):
        """Test yesterday is -1 days away."""
        yesterday = date.today() - timedelta(days=1)
        assert days_until(yesterday) == -1

    def test_one_year_ahead(self):
        """Test calculating days to same date next year."""
        today = date.today()
        next_year = date(today.year + 1, today.month, today.day)
        days_diff = days_until(next_year)
        # Should be approximately 365 or 366 days
        assert days_diff in [365, 366]


class TestBusinessDaysBetween:
    """Tests for business_days_between function."""

    def test_monday_to_friday(self):
        """Test Mon-Fri inclusive is 5 business days."""
        # 2025-01-06 is Monday, 2025-01-10 is Friday
        assert business_days_between(date(2025, 1, 6), date(2025, 1, 10)) == 5

    def test_monday_to_sunday(self):
        """Test Mon-Sun includes only Mon-Fri."""
        # 2025-01-06 is Monday, 2025-01-12 is Sunday
        assert business_days_between(date(2025, 1, 6), date(2025, 1, 12)) == 5

    def test_saturday_and_sunday_only(self):
        """Test Sat-Sun returns 0 business days."""
        # 2025-01-11 is Saturday, 2025-01-12 is Sunday
        assert business_days_between(date(2025, 1, 11), date(2025, 1, 12)) == 0

    def test_weekend_single_date(self):
        """Test single weekend day returns 0."""
        # 2025-01-11 is Saturday
        assert business_days_between(date(2025, 1, 11), date(2025, 1, 11)) == 0

    def test_weekday_single_date(self):
        """Test single weekday returns 1."""
        # 2025-01-13 is Monday
        assert business_days_between(date(2025, 1, 13), date(2025, 1, 13)) == 1

    def test_start_greater_than_end_raises_error(self):
        """Test that start > end raises ValueError."""
        with pytest.raises(ValueError, match="start date must be less than or equal to end date"):
            business_days_between(date(2025, 1, 15), date(2025, 1, 10))

    def test_multiple_weeks(self):
        """Test business days across multiple weeks."""
        # Monday 2025-01-06 to Friday 2025-01-17 (2 full weeks)
        # Should be 10 business days (5 per week)
        assert business_days_between(date(2025, 1, 6), date(2025, 1, 17)) == 10

    def test_same_date_on_weekend(self):
        """Test same date on Saturday."""
        # 2025-01-11 is Saturday
        assert business_days_between(date(2025, 1, 11), date(2025, 1, 11)) == 0

    def test_friday_to_monday(self):
        """Test Friday to next Monday (includes weekend)."""
        # 2025-01-10 is Friday, 2025-01-13 is Monday
        assert business_days_between(date(2025, 1, 10), date(2025, 1, 13)) == 2

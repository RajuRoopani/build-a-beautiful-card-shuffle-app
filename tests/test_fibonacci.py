"""
test_fibonacci.py — Unit tests for the fibonacci module.

Run with:
    python -m pytest tests/test_fibonacci.py -v
"""

import pytest
from src.fibonacci.fibonacci import fibonacci


# ---------------------------------------------------------------------------
# Base Cases
# ---------------------------------------------------------------------------

class TestBaseCases:
    """Tests for base cases of the Fibonacci sequence."""

    def test_fibonacci_zero(self) -> None:
        """Test F(0) = 0."""
        assert fibonacci(0) == 0

    def test_fibonacci_one(self) -> None:
        """Test F(1) = 1."""
        assert fibonacci(1) == 1


# ---------------------------------------------------------------------------
# Small Values
# ---------------------------------------------------------------------------

class TestSmallValues:
    """Tests for small Fibonacci values."""

    def test_fibonacci_two(self) -> None:
        """Test F(2) = 1."""
        assert fibonacci(2) == 1

    def test_fibonacci_three(self) -> None:
        """Test F(3) = 2."""
        assert fibonacci(3) == 2

    def test_fibonacci_five(self) -> None:
        """Test F(5) = 5."""
        assert fibonacci(5) == 5


# ---------------------------------------------------------------------------
# Larger Values
# ---------------------------------------------------------------------------

class TestLargerValues:
    """Tests for larger Fibonacci values."""

    def test_fibonacci_ten(self) -> None:
        """Test F(10) = 55."""
        assert fibonacci(10) == 55

    def test_fibonacci_twenty(self) -> None:
        """Test F(20) = 6765."""
        assert fibonacci(20) == 6765

    def test_fibonacci_thirty(self) -> None:
        """Test F(30) = 832040."""
        assert fibonacci(30) == 832040


# ---------------------------------------------------------------------------
# Negative Input Error
# ---------------------------------------------------------------------------

class TestNegativeInputError:
    """Tests that negative inputs raise ValueError."""

    def test_fibonacci_negative_one_raises_value_error(self) -> None:
        """Test that fibonacci(-1) raises ValueError."""
        with pytest.raises(ValueError, match="must be non-negative"):
            fibonacci(-1)

    def test_fibonacci_negative_five_raises_value_error(self) -> None:
        """Test that fibonacci(-5) raises ValueError."""
        with pytest.raises(ValueError, match="must be non-negative"):
            fibonacci(-5)

    def test_fibonacci_large_negative_raises_value_error(self) -> None:
        """Test that large negative input raises ValueError."""
        with pytest.raises(ValueError, match="must be non-negative"):
            fibonacci(-100)


# ---------------------------------------------------------------------------
# Non-Integer Input Error
# ---------------------------------------------------------------------------

class TestNonIntegerInputError:
    """Tests that non-integer inputs raise TypeError."""

    def test_fibonacci_float_raises_type_error(self) -> None:
        """Test that fibonacci(3.5) raises TypeError."""
        with pytest.raises(TypeError, match="must be an integer"):
            fibonacci(3.5)

    def test_fibonacci_string_raises_type_error(self) -> None:
        """Test that fibonacci('5') raises TypeError."""
        with pytest.raises(TypeError, match="must be an integer"):
            fibonacci("5")

    def test_fibonacci_none_raises_type_error(self) -> None:
        """Test that fibonacci(None) raises TypeError."""
        with pytest.raises(TypeError, match="must be an integer"):
            fibonacci(None)

    def test_fibonacci_list_raises_type_error(self) -> None:
        """Test that fibonacci([5]) raises TypeError."""
        with pytest.raises(TypeError, match="must be an integer"):
            fibonacci([5])

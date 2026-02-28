"""
test_calculator.py — Unit tests for the calculator module.

Run with:
    python -m pytest tests/
"""

import pytest
from src.calculator.calculator import add, subtract, multiply, divide


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

class TestAdd:
    def test_add_positive_numbers(self) -> None:
        assert add(3.0, 4.0) == 7.0

    def test_add_negative_numbers(self) -> None:
        assert add(-1.0, -2.0) == -3.0

    def test_add_mixed_sign(self) -> None:
        assert add(-5.0, 3.0) == -2.0

    def test_add_floats(self) -> None:
        assert add(0.1, 0.2) == pytest.approx(0.3)

    def test_add_zero(self) -> None:
        assert add(0.0, 0.0) == 0.0


# ---------------------------------------------------------------------------
# subtract
# ---------------------------------------------------------------------------

class TestSubtract:
    def test_subtract_positive_numbers(self) -> None:
        assert subtract(10.0, 4.0) == 6.0

    def test_subtract_resulting_in_negative(self) -> None:
        assert subtract(2.0, 5.0) == -3.0

    def test_subtract_negative_from_negative(self) -> None:
        assert subtract(-3.0, -1.0) == -2.0

    def test_subtract_floats(self) -> None:
        assert subtract(1.5, 0.5) == pytest.approx(1.0)

    def test_subtract_zero(self) -> None:
        assert subtract(7.0, 0.0) == 7.0


# ---------------------------------------------------------------------------
# multiply
# ---------------------------------------------------------------------------

class TestMultiply:
    def test_multiply_positive_numbers(self) -> None:
        assert multiply(3.0, 4.0) == 12.0

    def test_multiply_by_zero(self) -> None:
        assert multiply(99.0, 0.0) == 0.0

    def test_multiply_negative_numbers(self) -> None:
        assert multiply(-2.0, -3.0) == 6.0

    def test_multiply_mixed_sign(self) -> None:
        assert multiply(-4.0, 5.0) == -20.0

    def test_multiply_floats(self) -> None:
        assert multiply(2.5, 4.0) == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# divide
# ---------------------------------------------------------------------------

class TestDivide:
    def test_divide_positive_numbers(self) -> None:
        assert divide(10.0, 2.0) == 5.0

    def test_divide_resulting_in_float(self) -> None:
        assert divide(7.0, 2.0) == pytest.approx(3.5)

    def test_divide_negative_numerator(self) -> None:
        assert divide(-9.0, 3.0) == -3.0

    def test_divide_negative_denominator(self) -> None:
        assert divide(9.0, -3.0) == -3.0

    def test_divide_both_negative(self) -> None:
        assert divide(-8.0, -4.0) == 2.0

    def test_divide_by_zero_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Division by zero"):
            divide(5.0, 0.0)

    def test_divide_zero_numerator(self) -> None:
        assert divide(0.0, 5.0) == 0.0

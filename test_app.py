"""Test suite for Simple Calculator API (POST /calculate endpoint)."""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Literal


# Import app by reading the app.py file to avoid package import conflict
import sys
import importlib.util
from pathlib import Path

app_path = Path(__file__).parent / "app.py"
spec = importlib.util.spec_from_file_location("app_calculator", app_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = app_module.app


client = TestClient(app)


class TestAddOperation:
    """Tests for the add operation."""

    def test_add_positive_numbers(self) -> None:
        """Test adding two positive numbers."""
        response = client.post(
            "/calculate",
            json={"operation": "add", "a": 1, "b": 2}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 3.0}

    def test_add_with_floats(self) -> None:
        """Test adding floating point numbers."""
        response = client.post(
            "/calculate",
            json={"operation": "add", "a": 1.5, "b": 2.5}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 4.0}

    def test_add_negative_numbers(self) -> None:
        """Test adding negative numbers: -5 + 3 = -2."""
        response = client.post(
            "/calculate",
            json={"operation": "add", "a": -5, "b": 3}
        )
        assert response.status_code == 200
        assert response.json() == {"result": -2.0}

    def test_add_with_zero(self) -> None:
        """Test adding with zero."""
        response = client.post(
            "/calculate",
            json={"operation": "add", "a": 0, "b": 5}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 5.0}


class TestSubtractOperation:
    """Tests for the subtract operation."""

    def test_subtract_positive_numbers(self) -> None:
        """Test subtracting two positive numbers: 5 - 3 = 2."""
        response = client.post(
            "/calculate",
            json={"operation": "subtract", "a": 5, "b": 3}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 2.0}

    def test_subtract_resulting_negative(self) -> None:
        """Test subtraction resulting in a negative number."""
        response = client.post(
            "/calculate",
            json={"operation": "subtract", "a": 3, "b": 5}
        )
        assert response.status_code == 200
        assert response.json() == {"result": -2.0}

    def test_subtract_with_floats(self) -> None:
        """Test subtracting floating point numbers."""
        response = client.post(
            "/calculate",
            json={"operation": "subtract", "a": 5.5, "b": 2.5}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 3.0}

    def test_subtract_with_zero(self) -> None:
        """Test subtracting zero."""
        response = client.post(
            "/calculate",
            json={"operation": "subtract", "a": 5, "b": 0}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 5.0}


class TestMultiplyOperation:
    """Tests for the multiply operation."""

    def test_multiply_positive_numbers(self) -> None:
        """Test multiplying two positive numbers: 4 * 3 = 12."""
        response = client.post(
            "/calculate",
            json={"operation": "multiply", "a": 4, "b": 3}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 12.0}

    def test_multiply_with_negative(self) -> None:
        """Test multiplying with a negative number."""
        response = client.post(
            "/calculate",
            json={"operation": "multiply", "a": -4, "b": 3}
        )
        assert response.status_code == 200
        assert response.json() == {"result": -12.0}

    def test_multiply_by_zero(self) -> None:
        """Test multiplying by zero."""
        response = client.post(
            "/calculate",
            json={"operation": "multiply", "a": 100, "b": 0}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 0.0}

    def test_multiply_with_floats(self) -> None:
        """Test multiplying floating point numbers."""
        response = client.post(
            "/calculate",
            json={"operation": "multiply", "a": 2.5, "b": 4}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 10.0}

    def test_multiply_two_negative_numbers(self) -> None:
        """Test multiplying two negative numbers."""
        response = client.post(
            "/calculate",
            json={"operation": "multiply", "a": -4, "b": -3}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 12.0}


class TestErrorHandling:
    """Tests for error handling and invalid inputs."""

    def test_invalid_operation_returns_422(self) -> None:
        """Test that an invalid operation returns 422 Unprocessable Entity."""
        response = client.post(
            "/calculate",
            json={"operation": "divide", "a": 1, "b": 2}
        )
        assert response.status_code == 422

    def test_missing_operation_field_returns_422(self) -> None:
        """Test that missing operation field returns 422."""
        response = client.post(
            "/calculate",
            json={"a": 1, "b": 2}
        )
        assert response.status_code == 422

    def test_missing_a_field_returns_422(self) -> None:
        """Test that missing 'a' field returns 422."""
        response = client.post(
            "/calculate",
            json={"operation": "add", "b": 2}
        )
        assert response.status_code == 422

    def test_missing_b_field_returns_422(self) -> None:
        """Test that missing 'b' field returns 422."""
        response = client.post(
            "/calculate",
            json={"operation": "add", "a": 1}
        )
        assert response.status_code == 422

    def test_invalid_operation_modulo(self) -> None:
        """Test that modulo operation (not allowed) returns 422."""
        response = client.post(
            "/calculate",
            json={"operation": "modulo", "a": 10, "b": 3}
        )
        assert response.status_code == 422

    def test_invalid_operation_power(self) -> None:
        """Test that power operation (not allowed) returns 422."""
        response = client.post(
            "/calculate",
            json={"operation": "power", "a": 2, "b": 3}
        )
        assert response.status_code == 422

    def test_empty_operation_string_returns_422(self) -> None:
        """Test that empty operation string returns 422."""
        response = client.post(
            "/calculate",
            json={"operation": "", "a": 1, "b": 2}
        )
        assert response.status_code == 422


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_very_large_numbers(self) -> None:
        """Test operations with very large numbers."""
        response = client.post(
            "/calculate",
            json={"operation": "add", "a": 1e10, "b": 2e10}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 3e10}

    def test_very_small_numbers(self) -> None:
        """Test operations with very small numbers."""
        response = client.post(
            "/calculate",
            json={"operation": "add", "a": 1e-10, "b": 2e-10}
        )
        assert response.status_code == 200
        result = response.json()["result"]
        assert abs(result - 3e-10) < 1e-15

    def test_float_precision_addition(self) -> None:
        """Test floating point precision in addition (0.1 + 0.2)."""
        response = client.post(
            "/calculate",
            json={"operation": "add", "a": 0.1, "b": 0.2}
        )
        assert response.status_code == 200
        result = response.json()["result"]
        # Use approximate equality for floating point
        assert abs(result - 0.3) < 1e-9

    def test_subtract_same_numbers_equals_zero(self) -> None:
        """Test that subtracting identical numbers equals zero."""
        response = client.post(
            "/calculate",
            json={"operation": "subtract", "a": 42, "b": 42}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 0.0}

    def test_multiply_by_one(self) -> None:
        """Test multiplying by one (identity element)."""
        response = client.post(
            "/calculate",
            json={"operation": "multiply", "a": 999, "b": 1}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 999.0}

    def test_negative_zero_handling(self) -> None:
        """Test handling of negative zero."""
        response = client.post(
            "/calculate",
            json={"operation": "add", "a": -5, "b": 5}
        )
        assert response.status_code == 200
        assert response.json() == {"result": 0.0}

    def test_integer_inputs_return_float_output(self) -> None:
        """Test that integer inputs return float outputs."""
        response = client.post(
            "/calculate",
            json={"operation": "add", "a": 2, "b": 3}
        )
        assert response.status_code == 200
        result = response.json()["result"]
        assert isinstance(result, float)
        assert result == 5.0

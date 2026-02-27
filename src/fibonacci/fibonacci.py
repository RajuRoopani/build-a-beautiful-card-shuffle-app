"""
fibonacci.py — Fibonacci number calculation module.
"""


def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number using iterative approach.

    Returns the nth Fibonacci number using 0-indexed convention where
    F(0) = 0, F(1) = 1, and F(n) = F(n-1) + F(n-2) for n > 1.
    Uses an iterative implementation for efficiency.

    Args:
        n: The index of the Fibonacci number to calculate (must be non-negative integer).

    Returns:
        The nth Fibonacci number as an integer.

    Raises:
        TypeError: If n is not an integer (e.g., float, string, or other non-integer type).
        ValueError: If n is negative.

    Examples:
        >>> fibonacci(0)
        0
        >>> fibonacci(1)
        1
        >>> fibonacci(2)
        1
        >>> fibonacci(5)
        5
        >>> fibonacci(10)
        55
    """
    # Check type first: reject floats, strings, etc.
    # Note: bool is a subclass of int in Python, so isinstance(True, int) is True
    # We accept bools as valid input per the requirements
    if not isinstance(n, int):
        raise TypeError(f"fibonacci() argument must be an integer, not {type(n).__name__}")

    # Check for negative values
    if n < 0:
        raise ValueError("fibonacci() argument must be non-negative")

    # Base cases
    if n == 0:
        return 0
    if n == 1:
        return 1

    # Iterative calculation for n >= 2
    prev, curr = 0, 1
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr

    return curr

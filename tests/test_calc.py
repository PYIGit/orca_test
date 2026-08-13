import math

import pytest

from src.calc import MAX_N, factorial


def test_factorial_zero_and_one():
    assert factorial(0) == 1
    assert factorial(1) == 1


def test_factorial_positive():
    assert factorial(5) == 120
    assert factorial(10) == 3628800


@pytest.mark.parametrize("n", [2, 3, 7, 12, 20])
def test_factorial_matches_math_factorial(n):
    assert factorial(n) == math.factorial(n)


def test_factorial_negative_raises():
    with pytest.raises(ValueError, match="non-negative"):
        factorial(-1)


@pytest.mark.parametrize("n", [-2, -10, -1000])
def test_factorial_various_negatives_raise(n):
    with pytest.raises(ValueError, match="non-negative"):
        factorial(n)


def test_max_n_boundary_is_allowed():
    assert factorial(MAX_N) == math.factorial(MAX_N)


def test_factorial_above_max_n_raises():
    with pytest.raises(ValueError, match=f"at most {MAX_N}"):
        factorial(MAX_N + 1)


@pytest.mark.parametrize("n", [MAX_N + 1, MAX_N + 100, 10 ** 6])
def test_factorial_various_too_large_raise(n):
    with pytest.raises(ValueError, match="at most"):
        factorial(n)

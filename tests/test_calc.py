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


def test_factorial_large_negative_raises():
    with pytest.raises(ValueError, match="non-negative"):
        factorial(-MAX_N)


def test_factorial_at_upper_bound_is_allowed():
    assert factorial(MAX_N) == math.factorial(MAX_N)


def test_factorial_above_upper_bound_raises():
    with pytest.raises(ValueError, match=f"<= {MAX_N}"):
        factorial(MAX_N + 1)


@pytest.mark.parametrize("n", [MAX_N + 2, MAX_N * 10, MAX_N**2])
def test_factorial_far_above_upper_bound_raises(n):
    with pytest.raises(ValueError, match=f"<= {MAX_N}"):
        factorial(n)


def test_max_n_parameter_defaults_to_module_constant():
    assert factorial(5) == factorial(5, MAX_N)
    with pytest.raises(ValueError, match=f"<= {MAX_N}"):
        factorial(MAX_N + 1)


@pytest.mark.parametrize("limit", [0, 1, 5, 100, MAX_N * 3])
def test_max_n_parameter_allows_values_up_to_custom_limit(limit):
    assert factorial(limit, MAX_N=limit) == math.factorial(limit)


@pytest.mark.parametrize("limit", [0, 1, 5, 100])
def test_max_n_parameter_rejects_values_above_custom_limit(limit):
    with pytest.raises(ValueError, match=f"<= {limit}"):
        factorial(limit + 1, MAX_N=limit)


def test_max_n_parameter_can_raise_limit_above_default():
    n = MAX_N + 1
    assert factorial(n, MAX_N=n) == math.factorial(n)


def test_max_n_parameter_can_lower_limit_below_default():
    with pytest.raises(ValueError, match="<= 10"):
        factorial(11, MAX_N=10)


def test_max_n_parameter_accepts_positional_argument():
    assert factorial(7, 7) == math.factorial(7)
    with pytest.raises(ValueError, match="<= 6"):
        factorial(7, 6)


def test_max_n_parameter_does_not_bypass_negative_check():
    with pytest.raises(ValueError, match="non-negative"):
        factorial(-1, MAX_N=MAX_N * 2)


def test_max_n_parameter_does_not_mutate_module_constant():
    factorial(3, MAX_N=3)
    assert MAX_N == 1000
    with pytest.raises(ValueError, match=f"<= {MAX_N}"):
        factorial(MAX_N + 1)

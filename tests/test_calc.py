import math

import pytest

from src.calc import factorial


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


# --- T3: 큰 입력 회귀 방지 ---


@pytest.mark.parametrize("n", [100, 1000])
def test_factorial_large_input(n):
    assert factorial(n) == math.factorial(n)


# --- T1: 비정수 입력은 부호와 무관하게 TypeError (J1 선택지 A) ---


@pytest.mark.parametrize("value", [2.5, 3.0, "3", None, [], object()])
def test_factorial_non_int_raises_type_error(value):
    with pytest.raises(TypeError, match="must be an int"):
        factorial(value)


def test_factorial_negative_float_reports_type_not_sign():
    """-2.5는 부호가 아니라 타입이 문제이므로 TypeError여야 한다.

    이전 구현은 부호 검사가 먼저라 ValueError("non-negative")를 냈고,
    호출자가 메시지를 따라 2.5로 고치면 그제서야 TypeError가 나 오진을 유발했다.
    """
    with pytest.raises(TypeError, match="got float"):
        factorial(-2.5)


def test_factorial_type_error_message_names_actual_type():
    with pytest.raises(TypeError, match="got str"):
        factorial("5")


# --- T2: 반환 타입 및 bool 계약 (stdlib 정합) ---


def test_factorial_returns_int():
    assert isinstance(factorial(5), int)


@pytest.mark.parametrize("value, expected", [(True, 1), (False, 1)])
def test_factorial_accepts_bool_like_stdlib(value, expected):
    """bool은 int의 서브클래스라 통과시킨다 — math.factorial과 동일한 동작."""
    assert factorial(value) == expected
    assert factorial(value) == math.factorial(value)

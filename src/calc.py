print("first calc")

MAX_N = 1000


def factorial(n):
    """n의 팩토리얼을 반환한다.

    n이 음수이거나 MAX_N(1000)을 초과하면 ValueError를 던진다.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n > MAX_N:
        raise ValueError(f"n must be <= {MAX_N}")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def factorial(n):
    """n의 팩토리얼을 반환한다.

    n이 음수면 ValueError를 던진다.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

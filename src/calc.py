print("first calc")

MAX_N = 1000


def factorial(n, MAX_N=MAX_N):
    """n의 팩토리얼을 반환한다.

    n이 음수이거나 상한 MAX_N을 초과하면 ValueError를 던진다.

    상한값을 고정하는 대신 MAX_N 파라미터로 호출할 때마다 조정할 수 있다.
    생략하면 모듈 상수 MAX_N(1000)을 사용한다.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n > MAX_N:
        raise ValueError(f"n must be <= {MAX_N}")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

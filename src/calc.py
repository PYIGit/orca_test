def factorial(n: int) -> int:
    """n의 팩토리얼을 반환한다.

    `math.factorial`과 동일한 계약을 따른다. 즉 `int`가 아닌 입력은
    부호와 무관하게 `TypeError`이고, 음수 `int`만 `ValueError`다.
    `bool`은 `int`의 서브클래스이므로 `factorial(True)`는 1을 반환한다.

    Args:
        n: 팩토리얼을 구할 음이 아닌 정수.

    Returns:
        n의 팩토리얼. n이 0 또는 1이면 1.

    Raises:
        TypeError: n이 `int`가 아닌 경우.
        ValueError: n이 음수인 경우.

    Examples:
        >>> factorial(0)
        1
        >>> factorial(5)
        120
        >>> factorial(-1)
        Traceback (most recent call last):
            ...
        ValueError: n must be non-negative
        >>> factorial(2.5)
        Traceback (most recent call last):
            ...
        TypeError: n must be an int, got float
    """
    # 타입 검증을 부호 검증보다 앞에 둔다. 순서가 반대면 factorial(-2.5)가
    # 타입 문제인데도 "non-negative"라는 부호 메시지를 내보낸다.
    if not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n < 0:
        raise ValueError("n must be non-negative")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

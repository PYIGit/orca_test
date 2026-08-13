# calc

팩토리얼 계산 함수를 담은 작은 Python 학습용 프로젝트입니다.
구현 → 리뷰 → 문서 파이프라인 실습을 목적으로 합니다.

## 프로젝트 구조

```
.
├── src/
│   └── calc.py          # factorial 구현
├── tests/
│   └── test_calc.py     # pytest 테스트 (11개)
└── docs/
    └── REVIEW.md        # 누적 코드 리뷰 기록
```

## 요구 사항

- Python 3.12 (개발/검증 환경: 3.12.7)
- pytest (테스트 실행 시에만 필요)

외부 런타임 의존성은 없습니다. `src/calc.py`는 표준 라이브러리조차 import하지 않습니다.

## 사용법

프로젝트 루트에서:

```python
from src.calc import factorial

factorial(0)   # 1
factorial(5)   # 120
factorial(20)  # 2432902008176640000
```

Python 정수는 임의 정밀도이므로 큰 입력도 오버플로 없이 계산됩니다
(`factorial(1000)`은 2568자리 정수를 반환합니다).

## API

### `factorial(n)`

`n`의 팩토리얼을 반환합니다.

| 항목 | 내용 |
|---|---|
| 인자 | `n` — 0 이상의 정수 |
| 반환 | `int` — `n!` (`n=0`, `n=1`이면 `1`) |
| 예외 | `ValueError` — `n`이 음수일 때 (`"n must be non-negative"`) |

반복문 기반 구현이라 재귀 깊이 제한(`RecursionError`)이 없습니다.

#### 정수가 아닌 입력

현재 구현은 타입 검증을 하지 않으므로, 비정수 입력의 동작은 아래와 같이
내부 연산에서 새어 나온 결과입니다. **의도된 계약이 아닙니다.**

| 입력 | 실제 동작 |
|---|---|
| `2.5` | `TypeError: 'float' object cannot be interpreted as an integer` |
| `None`, `"5"` | `TypeError: '<' not supported between instances of ...` |
| `True` | `1`을 조용히 반환 (`bool`이 `int`의 서브클래스) |

`factorial(True)`가 예외 없이 값을 반환하는 점에 주의하세요.
자세한 논의는 [docs/REVIEW.md](docs/REVIEW.md)의 리뷰 #1, 3번 항목을 참고하세요.

## 테스트

프로젝트 루트에서 다음 명령으로 실행합니다:

```bash
python -m pytest -q
```

```
...........                                                              [100%]
11 passed in 0.06s
```

> **주의 — `pytest`를 직접 호출하면 실패합니다.**
>
> `tests/test_calc.py`는 `from src.calc import factorial`로 import하는데,
> 이 경로는 `sys.path`에 프로젝트 루트가 들어가야 해석됩니다.
> `python -m pytest`는 현재 디렉토리를 `sys.path`에 넣어주지만,
> `pytest` 실행 파일은 그렇지 않습니다.
>
> ```
> $ pytest -q
> E   ModuleNotFoundError: No module named 'src'
> ERROR tests/test_calc.py
> !!!!!! Interrupted: 1 error during collection !!!!!!
> ```
>
> 해결하려면 프로젝트 루트에 아래 설정을 추가하세요. 아직 적용되지 않은 상태입니다.
>
> ```toml
> # pyproject.toml
> [tool.pytest.ini_options]
> pythonpath = ["."]
> testpaths = ["tests"]
> ```

테스트는 경계값(0, 1), 일반 양수, `math.factorial`과의 대조(oracle) 검증,
음수 입력의 `ValueError` 경로를 덮습니다.

## 알려진 한계

- 패키징 설정(`pyproject.toml`, `src/__init__.py`)이 없어 `pytest` 단독 실행이 깨집니다.
- 타입 힌트가 없습니다 (`def factorial(n):`).
- 비정수 입력에 대한 명시적 검증이 없습니다 (위 표 참고).
- `.gitignore`가 없어 `__pycache__/`, `.pytest_cache/`가 워킹 트리에 남습니다.

전체 리뷰 내용과 조치 우선순위는 [docs/REVIEW.md](docs/REVIEW.md)에 정리되어 있습니다.

## 참고

기능적으로 `math.factorial`과 동일합니다. 학습 목적의 재구현이므로,
프로덕션 코드에서는 표준 라이브러리를 사용하는 편이 빠르고 안전합니다.

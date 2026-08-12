# orca_test

간단한 계산 유틸리티 모듈입니다. 현재 `src/calc.py`에 팩토리얼 함수 하나가 들어 있습니다.

## 요구사항

- Python 3.x (외부 의존성 없음) — 이 문서의 모든 예시는 Python 3.12.7에서 검증했습니다
- 테스트 실행 시에만 `pytest` 필요 (7.4.4에서 검증)

## 빠른 시작

저장소 루트에서 실행합니다.

```python
from src.calc import factorial

print(factorial(5))   # 120
print(factorial(0))   # 1
```

> `src` 패키지를 찾으려면 저장소 루트가 `sys.path`에 있어야 합니다.
> 다른 위치에서 실행한다면 `PYTHONPATH`에 저장소 루트를 추가하세요.
>
> ```bash
> # Linux / macOS
> PYTHONPATH=/path/to/repo python your_script.py
> ```
> ```powershell
> # Windows PowerShell
> $env:PYTHONPATH = "C:\path\to\repo"; python your_script.py
> ```
>
> 설정하지 않으면 `ModuleNotFoundError: No module named 'src'`가 납니다.

---

## API 레퍼런스

### `factorial(n)`

`n`의 팩토리얼(`n!`)을 반환합니다.

| 항목 | 내용 |
| --- | --- |
| 시그니처 | `factorial(n)` |
| 파라미터 | `n` — `0 <= n <= MAX_N`(1000) 범위의 정수 |
| 반환값 | `int` — `n!` (`0! == 1`) |
| 예외 | `n < 0`이면 `ValueError("n must be non-negative")`<br>`n > MAX_N`이면 `ValueError("n must be <= 1000")` |
| 구현 | 반복문 기반 (재귀 아님) |

#### 사용 예시

```python
from src.calc import factorial

factorial(0)    # 1
factorial(1)    # 1
factorial(5)    # 120
factorial(10)   # 3628800
factorial(20)   # 2432902008176640000
```

허용 범위를 벗어나면 양쪽 모두 `ValueError`가 발생합니다.
메시지는 서로 다르므로 어느 경계를 넘었는지 구분할 수 있습니다.

```python
try:
    factorial(-1)
except ValueError as e:
    print(e)    # n must be non-negative

try:
    factorial(1001)
except ValueError as e:
    print(e)    # n must be <= 1000
```

#### 큰 입력

Python의 정수는 임의 정밀도이므로 허용 범위 안에서는 오버플로 없이 정확한 값을 반환합니다.
`factorial(100)`은 158자리, 상한값인 `factorial(1000)`은 2568자리 정수입니다.

```python
len(str(factorial(100)))      # 158
len(str(factorial(MAX_N)))    # 2568
```

반복문 구현이라 재귀 깊이 제한(`RecursionError`)에 걸리지 않습니다.
입력 크기는 `MAX_N`으로 막혀 있어, 실수로 거대한 값을 넘겨 계산이 멈추는 상황은
예외로 걸러집니다. 1000을 넘는 팩토리얼이 필요하다면 표준 라이브러리의
`math.factorial`을 쓰세요 (상한이 없고 C 구현이라 더 빠릅니다).

### `MAX_N`

허용되는 최대 입력값인 모듈 레벨 상수로, 현재 값은 `1000`입니다.
함수와 함께 import할 수 있으므로, 값을 하드코딩하지 말고 이 상수를 참조하세요.

```python
from src.calc import MAX_N, factorial

MAX_N               # 1000
factorial(MAX_N)    # 계산됨 (2568자리)
```

---

## 동작 명세 (엣지 케이스)

아래는 실제 실행으로 확인한 결과입니다 (Python 3.12.7 기준).

| 입력 | 결과 |
| --- | --- |
| `factorial(0)` | `1` |
| `factorial(1)` | `1` |
| `factorial(1000)` | 정상 계산 (2568자리) — 상한 포함 |
| `factorial(-1)` | `ValueError: n must be non-negative` |
| `factorial(1001)` | `ValueError: n must be <= 1000` |
| `factorial(5000)` | `ValueError: n must be <= 1000` |
| `factorial(2.0)` | `TypeError: 'float' object cannot be interpreted as an integer` |
| `factorial(3.5)` | `TypeError: 'float' object cannot be interpreted as an integer` |
| `factorial("3")` | `TypeError: '<' not supported between instances of 'str' and 'int'` |
| `factorial(None)` | `TypeError: '<' not supported between instances of 'NoneType' and 'int'` |
| `factorial(True)` | `1` (`factorial(1)`과 동일) |
| `factorial(False)` | `1` (`factorial(0)`과 동일) |

### 알아둘 점

- **상한은 경계값을 포함합니다.** 검사가 `n > MAX_N`이므로 `factorial(1000)`은
  정상 동작하고 `factorial(1001)`부터 거부됩니다.
- **타입 검증은 하지 않습니다.** 함수는 `n`이 정수인지 확인하지 않습니다.
  정수가 아닌 값은 위 표처럼 내부에서 `TypeError`로 새어 나오며,
  이는 의도적으로 설계된 예외 메시지가 아닙니다. 호출 전에 정수임을 보장하세요.
- **`2.0`처럼 값이 정수인 float도 거부됩니다.** 필요하다면 `factorial(int(x))`로 변환해서 넘기세요.
- **`bool`은 통과합니다.** Python에서 `bool`은 `int`의 하위 타입이라
  `factorial(True)`는 `factorial(1)`, `factorial(False)`는 `factorial(0)`과 같이 동작합니다.
  둘 다 결과가 `1`이라 눈에 잘 띄지 않으니, 플래그 값을 실수로 넘기지 않도록 주의하세요.
- **모듈을 import하면 `first calc`가 출력됩니다.**
  `src/calc.py` 최상단에 모듈 레벨 `print("first calc")`가 있어,
  `from src.calc import factorial`을 하는 것만으로 stdout에 한 줄이 찍힙니다.
  출력을 파싱하는 스크립트에서 사용할 때 주의하세요.

---

## 테스트

테스트는 `tests/test_calc.py`에 있으며 14개의 케이스를 검증합니다.
경계값(`0`, `1`, `MAX_N`), 일반 양수, `math.factorial`과의 대조,
그리고 양쪽 경계를 벗어난 입력의 예외 메시지까지 덮습니다.

저장소 루트에서 다음과 같이 실행합니다.

```bash
python -m pytest tests/ -q
```

```
..............                                                           [100%]
14 passed
```

> **반드시 `python -m pytest` 형태로 실행하세요.**
> `pytest tests/`처럼 바로 실행하면 저장소 루트가 `sys.path`에 추가되지 않아
> `ModuleNotFoundError: No module named 'src'`로 수집 단계에서 실패합니다.
> `python -m` 형태는 현재 디렉터리를 `sys.path`에 넣어주기 때문에 정상 동작합니다.

## 프로젝트 구조

```
.
├── README.md            # 이 문서 (사용법 + API 레퍼런스)
├── REVIEW.md            # 코드 리뷰 리포트 (알려진 이슈)
├── src/
│   └── calc.py          # factorial 구현
└── tests/
    └── test_calc.py     # factorial 테스트
```

패키징 설정(`pyproject.toml`, `setup.py`)이나 `conftest.py`는 없습니다.
그래서 위 "빠른 시작"과 "테스트" 항목의 `sys.path` 주의사항이 필요합니다.

## 알려진 이슈

자세한 분석은 [`REVIEW.md`](REVIEW.md)에 있습니다. 사용자 입장에서 영향이 있는 것만 요약하면:

| 이슈 | 영향 |
| --- | --- |
| `pytest tests/` 직접 실행 시 수집 실패 | `python -m pytest`로 실행하면 회피됩니다 |
| import 시 `first calc` 표준출력 | stdout을 파싱하는 스크립트에서 주의 |
| 비정수 입력에 대한 타입 검증 없음 | 호출 전에 정수임을 보장해야 합니다 |

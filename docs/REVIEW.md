# 코드 리뷰 기록

이 문서는 `src/calc.py`와 `tests/test_calc.py`에 대한 리뷰를 누적 기록한다.
새 리뷰는 항상 문서 맨 아래에 `## 리뷰 #N` 형태로 추가하며, 기존 내용은 수정하지 않는다.

---

## 리뷰 #1

- **일시**: 2026-08-13
- **대상**: `src/calc.py`, `tests/test_calc.py`
- **기준 커밋**: `a999ba2` (디렉토리 초기화)
- **테스트 결과**: `python -m pytest -q` → **11 passed** (0.04s)

### 요약

`factorial` 구현 자체는 정확하고 간결하다. 반복문 기반이라 재귀 깊이 제한이 없고,
`result = 1` + `range(2, n+1)`로 `n=0`, `n=1`을 별도 분기 없이 자연스럽게 처리한다.
테스트도 정상값·경계값·예외 경로를 고루 덮고 있다.

가장 큰 문제는 코드가 아니라 **패키징/실행 환경**이다. 현재 테스트는
`python -m pytest`로 실행할 때만 통과하고, 일반적인 `pytest` 명령으로는 수집 단계에서 실패한다.

### 발견 사항

#### [High] 1. `pytest` 단독 실행 시 테스트 수집 실패

`tests/test_calc.py:5`의 `from src.calc import factorial`이 `python -m pytest`에서만 동작한다.
`python -m`은 현재 디렉토리를 `sys.path`에 넣어주지만, `pytest` 실행 파일을 직접 호출하면 그렇지 않다.

실제 재현 결과:

```
$ pytest -q
E   ModuleNotFoundError: No module named 'src'
ERROR tests/test_calc.py
!!!!!! Interrupted: 1 error during collection !!!!!!
```

CI나 다른 개발자의 로컬 환경에서 바로 깨질 수 있는 구성이다.

권장 조치 — 아래 중 하나를 선택:

```toml
# pyproject.toml (권장)
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

또는 프로젝트 루트에 빈 `conftest.py`를 두고 `src/__init__.py`를 추가해 정식 패키지로 만든다.

#### [Medium] 2. 타입 힌트 부재

`def factorial(n):`에는 시그니처 정보가 없다. 정수 전용 함수임을 명시하면
IDE 자동완성과 정적 분석(mypy 등)에서 이득이 있다.

```python
def factorial(n: int) -> int:
```

#### [Medium] 3. 정수가 아닌 입력에 대한 계약이 불명확

현재 동작을 직접 확인한 결과:

| 입력 | 결과 |
|---|---|
| `2.5` | `TypeError: 'float' object cannot be interpreted as an integer` |
| `3.0` | `TypeError: 'float' object cannot be interpreted as an integer` |
| `True` | `1` (정상 반환) |

- `TypeError`는 함수가 의도적으로 던진 것이 아니라 내부 `range()`에서 새어 나온 메시지다.
  호출자 입장에서 원인 파악이 어렵다.
- `factorial(True)`가 조용히 `1`을 반환하는 것은 `bool`이 `int`의 서브클래스이기 때문이며,
  버그를 숨길 수 있는 경로다.

`n < 0` 검사 앞에 명시적 타입 검증을 추가하는 것을 권한다.

```python
if not isinstance(n, int) or isinstance(n, bool):
    raise TypeError("n must be an int")
```

참고: `float`에 대해 `TypeError`를 내는 동작 자체는 `math.factorial`과 동일하므로,
"stdlib과 동일한 계약을 따른다"고 판단한다면 메시지 개선만 해도 된다.

#### [Low] 4. 독스트링 형식

동작 설명은 충분하나 `Args` / `Returns` / `Raises` 절이 없다.
`Raises: ValueError` 정보가 본문 문장에만 있어 자동 문서화 도구가 인식하지 못한다.
doctest 예시(`>>> factorial(5)` → `120`)를 넣으면 문서와 테스트를 함께 얻을 수 있다.

#### [Low] 5. 표준 라이브러리 중복

기능적으로는 `math.factorial`과 동일하다. 실습/학습 목적의 재구현이라면 문제없으나,
프로덕션 코드라면 stdlib을 쓰는 편이 빠르고 안전하다.
현 코드는 학습 맥락으로 보이므로 **변경 불필요**로 판단한다.

#### [Low] 6. `.gitignore` 부재

`src/__pycache__/`, `tests/__pycache__/`, `.pytest_cache/`가 워킹 트리에 그대로 남아 있다.
`.gitignore`가 없어 실수로 커밋될 위험이 있다.

### 테스트 코드 평가

**좋은 점**

- `test_factorial_zero_and_one` — 경계값(0, 1)을 정확히 짚었다.
- `test_factorial_matches_math_factorial` — `math.factorial`을 기준(oracle)으로 삼은
  파라미터화 테스트는 하드코딩된 기댓값보다 견고하다.
- `pytest.raises(ValueError, match="non-negative")` — 예외 타입뿐 아니라
  메시지까지 검증해 정확도가 높다.
- 음수 케이스를 `-1` 단독 테스트와 `[-2, -10, -1000]` 파라미터화로 나눠 덮었다.

**보완 제안**

1. 비정수 입력(`2.5`, `True`, `None`, `"5"`)에 대한 테스트가 없다.
   위 3번 항목의 계약을 정한 뒤 그에 맞는 테스트를 추가할 것.
2. 반환 타입 검증(`assert isinstance(factorial(5), int)`)이 없다.
   `bool` 입력 문제와도 연결된다.
3. 큰 입력(예: `n=1000`) 테스트가 없다. Python 정수는 임의 정밀도라
   오버플로는 없지만, 반복문 구현이 큰 값에서도 정확한지 확인할 가치가 있다.

### 조치 우선순위

| 순위 | 항목 | 심각도 |
|---|---|---|
| 1 | `pythonpath` 설정으로 `pytest` 실행 정상화 | High |
| 2 | 비정수 입력 계약 확정 + 타입 검증 추가 | Medium |
| 3 | 타입 힌트 추가 | Medium |
| 4 | 비정수/반환타입 테스트 보강 | Medium |
| 5 | 독스트링 정비, `.gitignore` 추가 | Low |

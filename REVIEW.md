# 코드 리뷰 리포트 — `src/calc.py`, `tests/test_calc.py`

- **리뷰 대상**: `e85df72` + 미커밋 작업분 (`src/calc.py`, `tests/test_calc.py` 미추적)
- **브랜치**: `PYIGit/pipeline`
- **리뷰 일자**: 2026-08-11 (2차 — 코드 갱신분 재리뷰, 1차 리포트를 대체함)
- **검증 환경**: Python 3.12.7 (Anaconda), pytest 7.4.4

> 이 문서는 같은 파일들의 1차 리뷰 이후 코드가 수정되어(`src/calc.py` 16:41,
> `tests/test_calc.py` 17:45) 현재 내용 기준으로 다시 작성한 것이다.

---

## 1. 총평

1차 리뷰 이후 테스트 품질이 눈에 띄게 좋아졌다. `match=` 도입, 경계값 테스트,
`math.factorial`을 기준값으로 쓰는 차분 테스트가 추가되어 뮤테이션 검출률이
**6/7 → 13/15**로 올랐다. `MAX_N` 상한 도입도 무한 입력 방어로서 타당하다.

반면 **1차에서 지적한 High 이슈는 그대로 남아 있고**, `MAX_N` 도입이 기존의
타입 계약 문제를 오히려 키웠다. 아래 H-1과 M-2가 이번 리뷰의 핵심이다.

### 1차 리뷰 지적사항 처리 현황

| 항목 | 상태 |
|---|---|
| H-1 실행 방식에 따른 수집 실패 | **미해결** (재현 확인) |
| M-1 `print` import 부작용 | **미해결** (재현 확인) |
| L-1 비정수 입력 계약 미정의 | **미해결 + 악화** → M-2 참고 |
| L-2 예외 메시지 미검증 | **해결** — `match=` 추가, 메시지 뮤테이션 검출됨 |
| Info README UTF-16 | **해결** — UTF-8로 재저장됨 |
| Info `.gitignore` 없음 | 미해결 |

### 이번 리뷰 요약

| 심각도 | 항목 |
|---|---|
| High | H-1. `pytest` 직접 실행 시 수집 실패 (잔존) |
| Medium | M-1. 모듈 최상단 `print` 부작용 (잔존) |
| Medium | M-2. 입력 크기에 따라 예외 타입이 갈림 (신규) |
| Low | L-3. `MAX_N` 값 자체를 검증하는 테스트가 없음 (신규) |
| Low | L-4. 상한 가드 회귀 시 테스트가 실패가 아니라 무한 대기 (신규) |
| Info | 테스트 중복, `.gitignore`, 잔여 파일 |

---

## 2. 발견 사항

### [High] H-1. `pytest`로 실행하면 여전히 수집 단계에서 실패한다 (잔존)

```
$ pytest tests -q
E   ModuleNotFoundError: No module named 'src'
!!!!! Interrupted: 1 error during collection !!!!!

$ python -m pytest tests -q
14 passed in 0.06s
```

`python -m pytest`는 현재 디렉터리를 `sys.path`에 넣지만 `pytest` 실행 파일은
넣지 않는다. 루트에 `conftest.py`도 `pyproject.toml`도 없어서 `src`를 찾지 못한다.
CI와 IDE 러너는 보통 `pytest`를 직접 호출하므로 **로컬 통과 / CI 실패**가 된다.

테스트가 14개로 늘어난 만큼 이 이슈의 체감 비용도 커졌다. 우선 처리를 권한다.

**수정안 (권장, 검증 완료)**
```toml
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```
최소 변경만 원하면 프로젝트 루트에 **빈 `conftest.py`** 한 개를 추가해도 된다.
두 방식 모두 적용 후 `pytest -q` → `14 passed` 확인했다.

---

### [Medium] M-1. 모듈 최상단 `print`가 그대로 남아 있다 (잔존)

```python
# src/calc.py:1
print("first calc")
```

`from src.calc import factorial` 시점에 stdout이 오염된다. 이 리뷰 중 함수를
호출할 때마다 `first calc`가 먼저 찍혔다. pytest는 출력을 캡처하므로 테스트가
14개로 늘어도 이 문제는 드러나지 않는다.

**수정안**: 삭제. 남겨야 하면 `if __name__ == "__main__":` 아래로 옮긴다.

---

### [Medium] M-2. `MAX_N` 도입으로 비정수 입력의 예외 타입이 크기에 따라 갈린다 (신규)

`MAX_N` 가드가 `range()`보다 먼저 실행되면서, **같은 종류의 잘못된 입력(float)이
값의 크기에 따라 다른 예외**를 던지게 됐다.

| 입력 | 실제 동작 |
|---|---|
| `2.5`, `3.0`, `999.5`, `1000.0` | `TypeError: 'float' object cannot be interpreted as an integer` |
| `1000.5`, `1001.0`, `inf` | `ValueError: n must be <= 1000` |
| `-0.5`, `-inf` | `ValueError: n must be non-negative` |
| `nan` | `TypeError` (모든 비교가 False라 두 가드를 통과) |
| `True` / `False` | `1` 반환 (bool이 int 서브클래스) |

문제가 되는 지점:

- **`factorial(-0.5)` → "n must be non-negative"**. 호출자가 `-0.5`를 `0.5`로
  고쳐도 여전히 실패한다. 진짜 원인은 부호가 아니라 정수가 아니라는 점인데
  메시지가 그걸 가린다.
- **`factorial(1000.5)` → "n must be <= 1000"**. 상한 문제로 보이지만
  `999.5`도 실패한다. 메시지가 오진을 유도한다.
- **`nan`은 두 가드를 모두 통과**한다. `nan < 0`과 `nan > MAX_N`이 둘 다 False라
  `range()`까지 내려가서야 터진다.
- docstring은 `ValueError`만 명시하는데 실제로는 `TypeError`도 나온다.

1차 리뷰 때는 모든 float가 일관되게 `TypeError`였으므로, 이는 `MAX_N` 추가로
새로 생긴 불일치다. 가드 앞에 타입 검사를 두면 한 번에 정리된다.

```python
def factorial(n):
    """n의 팩토리얼을 반환한다.

    n이 int가 아니면 TypeError, 음수이거나 MAX_N을 초과하면 ValueError를 던진다.
    """
    if not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n < 0:
        raise ValueError("n must be non-negative")
    if n > MAX_N:
        raise ValueError(f"n must be <= {MAX_N}")
    ...
```
이러면 `nan`·`inf`·`-0.5`·`'3'`·`None`이 모두 동일한 `TypeError`로 수렴한다.
`isinstance(n, int)`는 bool을 통과시키지만 `factorial(True) == 1! == 1`로
결과가 옳으므로 추가 방어는 과하다고 본다.

---

### [Low] L-3. `MAX_N`의 값 자체를 검증하는 테스트가 없다 (신규)

뮤테이션 테스트에서 `MAX_N`을 **999로 바꿔도, 1001로 바꿔도 14개 테스트가 전부
통과**했다 (부록 A의 유일한 생존자 2건).

원인은 테스트가 `MAX_N`을 모듈에서 import해 기대값을 그 상수로부터 유도하기
때문이다. `factorial(MAX_N)`, `factorial(MAX_N + 1)`, `match=f"<= {MAX_N}"`은
상수가 무엇으로 바뀌든 자동으로 따라간다.

상수를 import하는 것 자체는 매직 넘버를 없애는 좋은 습관이고, 상한 **메커니즘**은
정확히 검증되고 있다. 다만 1000이라는 **정책 값**은 아무도 지키지 않는다. 상한이
계약의 일부라면 값을 한 곳에서 못 박아두는 편이 좋다.

```python
def test_max_n_is_1000():
    """상한은 공개 계약이므로 값 변경은 의도적이어야 한다."""
    assert MAX_N == 1000
```

덧붙여 `MAX_N = 1000`의 **근거를 주석으로 남기는 것**을 권한다. 실측하면
`1000!`은 2568자리이고 계산에 0.6ms밖에 걸리지 않아, 성능 때문이라기엔 상당히
보수적인 값이다. 상한을 두는 판단 자체는 타당하나(L-4 참고) 왜 1000인지는
코드에서 읽히지 않는다.

> 참고: 상한 도입은 **동작 변경**이다. 이전에는 `factorial(5000)`이 계산됐고
> 지금은 `ValueError`다. 학습용 저장소라 문제없어 보이지만, 외부 호출자가 있다면
> 호환성 깨짐으로 다뤄야 한다.

---

### [Low] L-4. 상한 가드가 회귀하면 테스트가 실패가 아니라 무한 대기에 빠진다 (신규)

```python
# tests/test_calc.py:42
@pytest.mark.parametrize("n", [MAX_N + 2, MAX_N * 10, MAX_N**2])
def test_factorial_far_above_upper_bound_raises(n):
```

`MAX_N**2`은 1,000,000이다. 지금은 가드가 즉시 예외를 던지므로 순식간에 끝난다.
그러나 가드가 사라지면 이 테스트는 **실제로 `factorial(1_000_000)`을 계산한다**.
뮤테이션 실험에서 이 변종만 유일하게 실패가 아닌 **타임아웃(45초 초과 미완료)**으로
나왔다.

즉 상한 가드가 깨졌을 때 얻는 신호가 "빨간 테스트"가 아니라 "멈춘 CI 잡"이다.
후자는 원인 파악이 훨씬 번거롭다.

**수정안**: 커버리지를 줄이지 않고 신호만 바꾼다.

```python
@pytest.mark.parametrize("n", [MAX_N + 2, MAX_N * 10, MAX_N**2])
@pytest.mark.timeout(5)  # 가드 회귀 시 계산에 들어가지 않고 즉시 실패해야 한다
def test_factorial_far_above_upper_bound_raises(n):
    with pytest.raises(ValueError, match=f"<= {MAX_N}"):
        factorial(n)
```
`pytest-timeout` 도입이 부담이면 `MAX_N**2`만 빼도 위험은 사라진다.
`MAX_N * 10`(=10,000)까지는 최악의 경우에도 수십 ms 수준이다.

---

### [Info] 그 외

- **테스트 중복**: `test_factorial_positive`의 `5`, `10`은
  `test_factorial_matches_math_factorial`의 파라미터 집합과 성격이 겹친다.
  후자가 더 강한 검증(차분 비교)이므로 전자를 흡수해도 무리가 없다. 유지해도
  해는 없으니 취향 문제로 남긴다.
- **`.gitignore` 없음**: `src/__pycache__/`, `.pytest_cache/`가 계속 미추적으로
  노출된다.
- **잔여 파일 `orca`** (0바이트, 미추적)가 작업 트리에 남아 있다. 리뷰 대상과
  무관하며 셸 리다이렉션 사고로 보인다. 삭제 권장.

---

## 3. 잘된 점

1차 리뷰 이후 개선된 부분을 명시해 둔다.

- **`match=` 도입** — 예외 타입뿐 아니라 메시지까지 고정되어, 메시지 문구를
  바꾼 뮤테이션 2건이 모두 검출됐다. 1차의 유일한 생존자가 사라졌다.
- **`math.factorial` 차분 테스트** — 직접 계산한 기대값을 늘어놓는 대신 신뢰할 수
  있는 기준 구현과 비교한다. 적은 코드로 커버리지를 크게 넓히는 좋은 선택이다.
- **경계값 커버리지** — `MAX_N` 허용 / `MAX_N + 1` 거부를 양쪽에서 못 박아
  off-by-one 뮤테이션(`>=`, `> MAX_N + 1`)이 둘 다 잡혔다.
- **매직 넘버 제거** — 테스트가 `MAX_N`을 import해 쓰므로 상한 변경 시 테스트를
  일괄 수정할 필요가 없다 (다만 L-3의 트레이드오프가 있다).
- **구현 로직은 여전히 정확** — 반복문 기반이라 재귀 한계가 없고,
  `result = 1` + `range(2, n + 1)`로 `0!`, `1!`, `2!`가 특수 분기 없이 맞는다.
- **상한 가드 도입 판단 자체가 타당** — L-4에서 드러난 대로, 가드가 없으면
  큰 입력이 실제로 프로세스를 묶어버린다.

---

## 4. 권장 조치 순서

1. **H-1** — `pyproject.toml` 추가. CI 도입 전 필수.
2. **M-1** — `print("first calc")` 제거.
3. **M-2** — 가드 앞에 `isinstance` 검사 추가 + docstring에 `TypeError` 명시.
4. **L-4** — `MAX_N**2` 케이스에 타임아웃 부여 또는 제거.
5. **L-3** — `MAX_N` 값 고정 테스트 + 상한 근거 주석.
6. **Info** — `.gitignore` 추가, 잔여 파일 정리.

1~3번까지 반영하면 커밋 가능한 상태로 본다.

---

## 부록 A. 뮤테이션 테스트 결과

구현을 15가지로 변형한 뒤 현재 테스트 14개가 잡아내는지 측정했다.
파라미터화를 정확히 반영하기 위해 각 변종마다 실제 pytest를 실행했다.

| 변형 | 결과 |
|---|---|
| `range(2,n+1)` → `range(2,n)` | caught (7 failed) |
| `range(2,n+1)` → `range(3,n+1)` | caught (7 failed) |
| `result = 1` → `result = 0` | caught (8 failed) |
| `result *= i` → `result += i` | caught (6 failed) |
| 음수 가드 제거 | caught (2 failed) |
| `n < 0` → `n < -5` | caught (1 failed) |
| `n < 0` → `n <= 0` | caught (1 failed) |
| 음수 `ValueError` → `RuntimeError` | caught (2 failed) |
| 음수 메시지 문구 변경 | caught (2 failed) |
| **상한 가드 제거** | **caught — 단, 45초 내 미완료 (L-4)** |
| `n > MAX_N` → `n >= MAX_N` | caught (1 failed) |
| `n > MAX_N` → `n > MAX_N + 1` | caught (1 failed) |
| 상한 메시지 문구 변경 | caught (4 failed) |
| **`MAX_N` 1000 → 999** | ***SURVIVED** (14 passed) — L-3* |
| **`MAX_N` 1000 → 1001** | ***SURVIVED** (14 passed) — L-3* |

**검출률 13/15.** 1차 리뷰의 6/7에서 실질적으로 향상됐다.
생존자 2건은 모두 상한 값 미고정이라는 하나의 원인(L-3)에서 나온다.

## 부록 B. 재현 명령

```bash
# H-1 실패 재현
pytest tests -q

# 정상 통과
python -m pytest tests -q      # 14 passed
```

> 이 환경에서 `python`은 Microsoft Store 별칭 스텁으로 연결되어 아무것도 실행하지
> 않고 종료 코드 49를 반환한다. 실제 인터프리터는
> `C:/Users/young/anaconda3/python.exe`를 사용해야 한다.

뮤테이션 하니스: `<scratchpad>/mutate2.py`
(변종별 타임아웃 45초 필수 — 상한 가드 제거 변종이 끝나지 않기 때문이다.)

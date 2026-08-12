# 코드 리뷰 리포트 — `src/calc.py`, `tests/test_calc.py`

- **리뷰 대상**: `a2d8691` + 미커밋 작업분 (`src/calc.py`, `tests/test_calc.py` 수정됨)
- **브랜치**: `PYIGit/pipeline`
- **리뷰 일자**: 2026-08-12 (4차 — 이전 리포트를 대체함)
- **검증 환경**: Python 3.12 (`C:/Users/young/anaconda3/python.exe`), pytest 7.4.4
- **테스트 현황**: `python -m pytest tests -q` → **29 passed** (이전 14개)

---

## 1. 총평

3차 리뷰 이후 `factorial`의 시그니처가 `factorial(n)` → **`factorial(n, MAX_N=MAX_N)`**
으로 바뀌었다. 상한을 호출 시점에 조정할 수 있게 만든 변경이고, 테스트도 14개에서
29개로 늘면서 새 파라미터의 동작(기본값, 위치 인자, 음수 검사 우회 불가, 모듈 상수
불변)을 꼼꼼히 덮었다. **테스트 작성 자체는 이번에도 성실하다.**

문제는 **덮은 동작이 옳은 동작인지**다. `def factorial(n, MAX_N=MAX_N)`은 파라미터가
같은 이름의 모듈 상수를 섀도잉하고 기본값이 정의 시점에 고정되는 구조라, "상수를 한
곳에서 관리한다"는 기대가 조용히 깨진다(H-2). 그리고 상한은 원래 폭주 입력을 막는
**방어 장치**였는데 이제 호출자가 끄고 켤 수 있는 **옵션**이 됐다(M-3). 3차에서
L-4로 지적한 "가드가 없으면 프로세스가 수 분간 묶인다"는 위험이 이제 공개 API를 통해
정상 경로로 도달 가능해졌다.

한편 **이전 리뷰의 High/Medium은 이번에도 하나도 반영되지 않았다.** 새 기능은 추가됐지만
`pytest` 직접 실행 실패, 최상단 `print`, float 입력의 예외 타입 분기, `.pyc` 추적은
전부 그대로다. 유일하게 L-3(`MAX_N` 값 미고정)만 새 테스트 덕에 우연히 해소됐다.

### 이전 리뷰 지적사항 처리 현황

| 항목 | 상태 |
|---|---|
| H-1 `pytest` 직접 실행 시 수집 실패 | **미해결** (재현 확인) |
| N-1 `.pyc`가 git에 추적됨 | **미해결** (HEAD에 잔존) |
| M-1 모듈 최상단 `print` 부작용 | **미해결** (재현 확인) |
| M-2 입력 크기에 따라 예외 타입이 갈림 | **미해결 + 확대** → M-4 참고 |
| L-3 `MAX_N` 값 미고정 | **해결** — 뮤테이션 999/1001 모두 검출 |
| L-4 가드 회귀 시 장시간 정지 | **미해결** (60초 타임아웃 재확인) |

### 이번 리뷰 요약

| 심각도 | 항목 |
|---|---|
| High | H-1. `pytest` 직접 실행 시 수집 실패 (잔존) |
| High | **H-2. `MAX_N` 파라미터가 모듈 상수를 섀도잉 + 기본값 조기 바인딩 (신규)** |
| Medium | **M-3. 상한 가드를 호출자가 무력화할 수 있다 (신규)** |
| Medium | **M-4. `MAX_N` 인자 자체를 검증하지 않는다 (신규)** |
| Medium | **M-5. README가 새 시그니처를 반영하지 않는다 (신규)** |
| Medium | N-1. 빌드 산출물 `.pyc`가 git에 추적됨 (잔존) |
| Medium | M-1. 모듈 최상단 `print` 부작용 (잔존) |
| Medium | M-2. 비정수 입력의 예외 타입이 갈림 (잔존) |
| Low | L-4. 가드 회귀 시 실패가 아니라 장시간 정지 (잔존) |
| Low | **L-5. 파라미터 네이밍과 위치 인자 사용 (신규)** |

---

## 2. 발견 사항

### [High] H-2. `MAX_N` 파라미터가 모듈 상수를 섀도잉하고, 기본값이 정의 시점에 고정된다 (신규)

```python
# src/calc.py:6
def factorial(n, MAX_N=MAX_N):
```

이 한 줄에 두 가지 문제가 겹쳐 있다.

**(1) 기본값은 함수 정의 시점에 한 번 평가된다.** 이후 모듈 상수를 바꿔도 기본 동작은
따라오지 않는다. 실측 결과:

```python
import src.calc as calc
calc.MAX_N = 500
calc.factorial(600)      # 통과한다 (1409자리 값 반환)
calc.factorial.__defaults__   # (1000,) — 여전히 1000에 묶여 있음
```

상한을 500으로 낮췄다고 믿은 호출자에게 `factorial(600)`이 조용히 성공한다. 설정
오버라이드, 테스트 몽키패치, `importlib.reload` 없는 재설정이 모두 무력화된다.

**(2) 함수 본문 안에서 모듈 상수에 접근할 수 없다.** `MAX_N`이라는 이름이 파라미터로
가려져, 본문의 `n > MAX_N`과 `f"n must be <= {MAX_N}"`은 전부 파라미터를 가리킨다.
"기본값은 모듈 상수를 쓴다"는 관계가 시그니처의 `=MAX_N` 한 곳에만 존재하고,
그마저 조기 바인딩된 스냅샷이다.

**수정안** — 기본값을 `None`으로 두고 호출 시점에 상수를 읽는다. 이러면 섀도잉도
조기 바인딩도 동시에 사라진다.

```python
def factorial(n, *, max_n=None):
    """n의 팩토리얼을 반환한다.

    max_n을 생략하면 호출 시점의 모듈 상수 MAX_N을 상한으로 쓴다.
    """
    if max_n is None:
        max_n = MAX_N          # 본문에서 모듈 상수에 정상 접근
    ...
```

`test_max_n_parameter_defaults_to_module_constant`가 이 관계를 검증하려 하지만
`factorial(5) == factorial(5, MAX_N)` 형태라 두 값이 같은 스냅샷을 공유하는 한 항상
통과한다. 즉 **위 (1)의 결함을 잡지 못한다.** 수정 후에는 다음 테스트를 추가하면 잡힌다.

```python
def test_default_limit_follows_module_constant_at_call_time(monkeypatch):
    monkeypatch.setattr(calc, "MAX_N", 500)
    with pytest.raises(ValueError, match="<= 500"):
        calc.factorial(600)
```

---

### [Medium] M-3. 상한 가드를 호출자가 무력화할 수 있다 (신규)

`MAX_N`이 파라미터가 되면서, 3차 리뷰 L-4에서 "가드가 깨지면 프로세스가 묶인다"고
지적했던 경로가 **정상 API로 도달 가능**해졌다.

```python
factorial(50_000, MAX_N=10**9)   # 0.56초
factorial(20_000, MAX_N=10**9)   # 0.08초
```

실측하면 비용이 n에 대해 초선형으로 오르므로 `factorial(1_000_000, MAX_N=10**9)`은
수 분 이상 CPU를 점유한다. 상한이 **방어 장치**라면 호출자가 끌 수 있어서는 안 되고,
단순한 **편의 옵션**이라면 애초에 `math.factorial`이 상한 없이 더 빠르다.

지금 설계는 그 중간에 걸쳐 있어 두 목적 중 어느 쪽도 온전히 달성하지 못한다. 셋 중
하나를 고르길 권한다.

1. **방어가 목적이면** — 파라미터를 없애고 상한을 고정한다(변경 전 상태).
2. **조정이 목적이면** — 조정 가능한 상한에도 절대 천장을 둔다.
   ```python
   HARD_MAX_N = 100_000
   if max_n > HARD_MAX_N:
       raise ValueError(f"max_n must be <= {HARD_MAX_N}")
   ```
3. **상한이 불필요하다고 판단되면** — 가드를 걷어내고 `math.factorial` 위임을 검토한다.

> 참고: 이는 리뷰어의 설계 의견이다. "상한을 호출마다 조정 가능하게" 자체가 요구사항이라면
> 2번이 요구사항을 만족시키면서 폭주만 막는 최소 변경이다.

---

### [Medium] M-4. `MAX_N` 인자 자체를 검증하지 않는다 (신규)

새 파라미터에는 아무 검사가 없어서, 잘못된 상한이 **엉뚱한 대상을 탓하는 에러 메시지**로
새어 나온다. 실측 결과:

| 호출 | 실제 동작 |
|---|---|
| `factorial(5, -1)` | `ValueError: n must be <= -1` |
| `factorial(5, 0)` | `ValueError: n must be <= 0` |
| `factorial(5, 2.5)` | `ValueError: n must be <= 2.5` |
| `factorial(5, None)` | `TypeError: '>' not supported between instances of 'int' and 'NoneType'` |

메시지가 전부 **`n`을 문제 삼는다**. 그러나 `n = 5`는 완벽히 정상이고 잘못된 쪽은 상한이다.
`factorial(5, -1)`을 받은 호출자는 `n`을 고치려 들 텐데 무엇으로 바꿔도 실패한다.
`-1`은 어떤 `n`도 통과시킬 수 없는 값이므로 애초에 거부해야 한다.

이는 3차 리뷰의 M-2(비정수 `n`의 예외 타입이 값 크기에 따라 갈림)와 **같은 뿌리**이고,
새 파라미터가 그 표면적을 두 배로 넓혔다. 두 문제를 한 번에 정리하는 방향은 다음과 같다.

```python
def factorial(n, *, max_n=None):
    if max_n is None:
        max_n = MAX_N
    if not isinstance(max_n, int) or max_n < 0:
        raise ValueError(f"max_n must be a non-negative int, got {max_n!r}")
    if not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n < 0:
        raise ValueError("n must be non-negative")
    if n > max_n:
        raise ValueError(f"n must be <= {max_n}")
    ...
```

이러면 `n` 쪽 문제와 상한 쪽 문제가 서로 다른 메시지로 갈리고, `nan`·`inf`·`'3'`·`None`이
모두 일관된 `TypeError`로 수렴한다(M-2 동시 해소).

---

### [Medium] M-5. README가 새 시그니처를 반영하지 않는다 (신규)

코드는 바뀌었는데 문서가 따라오지 않아, 현재 README는 **틀린 API 레퍼런스**다.

| README 기재 | 실제 |
|---|---|
| `### factorial(n)` (39행) | `factorial(n, MAX_N=MAX_N)` |
| 시그니처 표 `factorial(n)` (45행) | 두 번째 파라미터 누락 |
| 파라미터 `n` 하나만 설명 (46행) | `MAX_N` 파라미터 미문서화 |
| "테스트는 … **14개**의 케이스를 검증합니다" (146행) | **29개** |
| 출력 예시 `14 passed` (158행) | `29 passed` |

새 기능이 문서에 전혀 없으므로 사용자는 존재 자체를 알 수 없고, 테스트 개수는 실제와
2배 이상 어긋난다. 구현·테스트·문서를 함께 굴리는 파이프라인이라면 문서 갱신을 같은
단위 작업에 묶는 편이 좋다.

M-3에서 시그니처를 다시 손볼 가능성이 있으므로, **설계를 확정한 뒤 문서를 한 번에**
갱신하길 권한다.

---

### [High] H-1. `pytest`로 실행하면 수집 단계에서 실패한다 (잔존)

```
$ pytest tests -q
E   ModuleNotFoundError: No module named 'src'
!!!!! Interrupted: 1 error during collection !!!!!

$ python -m pytest tests -q
29 passed in 0.09s
```

`python -m pytest`는 현재 디렉터리를 `sys.path`에 넣지만 `pytest` 실행 파일은 넣지
않는다. 루트에 `conftest.py`도 `pyproject.toml`도 없고 `src/`에 `__init__.py`도 없어
루트가 `sys.path`에 있어야만 import된다. CI와 IDE 러너는 보통 `pytest`를 직접
호출하므로 **로컬 통과 / CI 실패** 구조다.

테스트가 29개로 늘어난 만큼 이 이슈의 체감 비용도 커졌다.

**수정안 (권장, 검증 완료)**
```toml
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```
최소 변경만 원하면 프로젝트 루트에 **빈 `conftest.py`** 하나로도 된다.

---

### [Medium] N-1. 빌드 산출물 `.pyc`가 git에 추적되고 있다 (잔존)

`a2d8691`이 커밋한 `src/__pycache__/calc.cpython-312.pyc`와
`tests/__pycache__/test_calc.cpython-312-pytest-7.4.4.pyc`가 여전히 추적 대상이다.
3차 리뷰에서 확인한 두 가지 문제가 그대로다.

- 테스트를 한 번 돌리는 것만으로 작업 트리에 커밋 가능한 diff가 생긴다.
- 커밋된 바이트코드가 기록한 원본 크기(399바이트)가 같은 커밋의 `src/calc.py`(417바이트)와
  일치하지 않는다. 즉 최종 소스가 아닌 중간 버전의 산출물이 들어가 있다.

**수정안**
```bash
git rm -r --cached src/__pycache__ tests/__pycache__
```
```gitignore
# .gitignore
__pycache__/
*.py[cod]
.pytest_cache/
```

---

### [Medium] M-1. 모듈 최상단 `print`가 그대로 남아 있다 (잔존)

```python
# src/calc.py:1
print("first calc")
```

`from src.calc import factorial` 시점에 stdout이 오염된다. 이번 리뷰의 엣지 케이스
스크립트에서도 결과 앞에 `first calc`가 먼저 찍혔다. pytest는 출력을 캡처하므로
테스트가 29개로 늘어도 드러나지 않는다. README에 "모듈을 import하면 `first calc`가
출력됩니다"라고 문서화까지 되어 있어, 디버그 잔재가 명세로 승격된 상태다.

**수정안**: 삭제. 남겨야 하면 `if __name__ == "__main__":` 아래로 옮긴다.

---

### [Medium] M-2. 비정수 `n`의 예외 타입이 값의 크기에 따라 갈린다 (잔존)

| 입력 | 실제 동작 |
|---|---|
| `2.5`, `999.5`, `1000.0` | `TypeError: 'float' object cannot be interpreted as an integer` |
| `1000.5`, `inf` | `ValueError: n must be <= 1000` |
| `-0.5`, `-inf` | `ValueError: n must be non-negative` |
| `nan` | `TypeError` (모든 비교가 False라 두 가드를 통과) |
| `'3'`, `None` | `TypeError: '<' not supported between instances of ...` |

`factorial(999.5)`는 `TypeError`인데 `factorial(1000.5)`는 "n must be <= 1000"이다.
같은 종류의 잘못(정수가 아님)이 값의 크기에 따라 다른 진단을 받고, 후자의 메시지는
상한 문제라는 오진을 유도한다. docstring은 `ValueError`만 명시하는데 실제로는
`TypeError`도 난다. 수정안은 M-4에 통합해 제시했다.

---

### [Low] L-4. 상한 가드가 회귀하면 테스트가 실패가 아니라 장시간 정지에 빠진다 (잔존)

```python
# tests/test_calc.py:42
@pytest.mark.parametrize("n", [MAX_N + 2, MAX_N * 10, MAX_N**2])
```

`MAX_N**2`은 1,000,000이다. 상한 가드를 제거한 변종으로 실측하면 **60초 타임아웃까지
완료되지 않는다**(3차의 45초에서 60초로 늘려 재확인, `rc=124`). 가드가 깨졌을 때 얻는
신호가 "빨간 테스트"가 아니라 "멈춘 CI 잡"이다.

**수정안**
```python
@pytest.mark.parametrize("n", [MAX_N + 2, MAX_N * 10, MAX_N**2])
@pytest.mark.timeout(5)  # 가드 회귀 시 계산에 들어가지 않고 즉시 실패해야 한다
def test_factorial_far_above_upper_bound_raises(n):
```
`pytest-timeout` 도입이 부담이면 `MAX_N**2`만 빼도 위험은 사라진다.

---

### [Low] L-5. 파라미터 이름이 상수 규약을 쓰고, 위치 인자 사용이 테스트로 고정됐다 (신규)

- **ALL_CAPS 파라미터**: PEP 8에서 대문자 이름은 모듈 레벨 상수를 뜻한다. 파라미터에
  쓰면 읽는 사람이 상수로 오해하고, 실제로 H-2의 섀도잉을 눈에 안 띄게 만든다.
  `max_n`이 옳다.
- **위치 인자 호출**: `test_max_n_parameter_accepts_positional_argument`가
  `factorial(7, 7)`, `factorial(7, 6)`을 명시적으로 보장한다.

  ```python
  factorial(7, 6)   # 두 숫자 중 무엇이 상한인지 호출부만 봐서는 알 수 없다
  ```

  이 테스트가 있는 한 앞으로 keyword-only(`*`)로 좁히는 것이 **테스트를 깨는 변경**이
  된다. 지금은 아직 미커밋 상태이므로, 굳히기 전에 keyword-only로 정하는 편이 싸다.

---

### [Info] 그 외

- **L-3 해결 경위**: `MAX_N`을 999/1001로 바꾸는 뮤테이션이 이제 검출된다(각 1 failed).
  다만 이를 잡는 것은 `test_max_n_parameter_does_not_mutate_module_constant` 안의
  `assert MAX_N == 1000` 한 줄이다. 테스트 **이름은 "모듈 상수를 변경하지 않는다"**를
  뜻하는데 실제로는 상한 정책 값까지 고정하고 있어, 나중에 이 assert를 정리하다 보호가
  사라지기 쉽다. 의도를 이름에 드러낸 별도 테스트로 분리하길 권한다.
  ```python
  def test_max_n_is_1000():
      """상한은 공개 계약이므로 값 변경은 의도적이어야 한다."""
      assert MAX_N == 1000
  ```
- **테스트 비용이 상수에 연동됨**: `test_max_n_parameter_allows_values_up_to_custom_limit`의
  `MAX_N * 3`은 지금은 `factorial(3000)`(1ms)이지만, `MAX_N`을 올리면 비용이 초선형으로
  뛴다. `MAX_N = 100_000`이면 `factorial(300_000)`이 되어 수십 초가 걸린다. 고정 상수를
  쓰는 편이 안전하다.
- **`MAX_N = 1000`의 근거 주석 부재**: `1000!`은 2568자리이고 1ms도 안 걸려 성능 때문이라기엔
  보수적인 값이다. 왜 1000인지가 코드에서 읽히지 않는다.
- **타입 힌트 없음**: `def factorial(n: int, *, max_n: int | None = None) -> int:`를 붙이면
  M-4의 계약이 시그니처 수준에서 드러난다.
- **잔여 파일 `orca`** (0바이트, 미추적)가 작업 트리에 다시 생겼다. 3차에서도 지적했던
  셸 리다이렉션 사고로 보인다. 삭제 권장.

---

## 3. 잘된 점

- **새 파라미터의 테스트 커버리지가 성실하다** — 기본값, 커스텀 상한의 허용/거부 양쪽,
  기본값보다 높이기/낮추기, 위치 인자, 음수 검사 우회 불가, 모듈 상수 불변까지 8개
  테스트로 덮었다. 기능을 추가하면서 테스트를 같은 밀도로 따라 붙인 점은 좋다.
- **`test_max_n_parameter_does_not_bypass_negative_check`** — 새 파라미터가 기존 방어를
  뚫지 않는지 확인하는 발상이 특히 좋다. 기능 추가 시 놓치기 쉬운 각도다.
- **`math.factorial` 차분 테스트 확장** — 새 테스트에서도 기대값을 직접 적지 않고
  기준 구현과 대조한다. 적은 코드로 커버리지를 넓히는 좋은 습관이 유지됐다.
- **경계값 커버리지** — `limit`와 `limit + 1`을 양쪽에서 못 박아 off-by-one을 막는다.
- **L-3 해소** — 의도했든 아니든 상한 정책 값이 이제 테스트로 고정된다.
- **구현 로직은 여전히 정확** — 반복문 기반이라 재귀 한계가 없고, `result = 1` +
  `range(2, n + 1)`로 `0!`, `1!`, `2!`가 특수 분기 없이 맞는다.

---

## 4. 권장 조치 순서

**설계 결정이 먼저다.** M-3에서 제시한 세 방향 중 하나를 정해야 H-2·M-4·M-5·L-5가
한꺼번에 정리된다. 조정 가능한 상한을 유지하기로 한다면 다음 순서를 권한다.

1. **H-2 + M-4 + L-5** — 시그니처를 `def factorial(n, *, max_n=None)`으로 바꾸고,
   본문에서 `max_n is None`일 때 모듈 상수를 읽고, `max_n`과 `n`을 각각 검증한다.
   (섀도잉·조기 바인딩·미검증·네이밍·위치 인자가 한 번에 해결된다)
2. **M-3** — `HARD_MAX_N` 절대 천장을 추가해 폭주 입력을 막는다.
3. **N-1** — `.gitignore` 추가 + `git rm -r --cached __pycache__`.
4. **H-1** — `pyproject.toml` 추가. CI 도입 전 필수.
5. **M-1** — `print("first calc")` 제거.
6. **M-5** — 확정된 시그니처로 README 갱신 (파라미터 표, 테스트 개수, 예시 출력).
7. **L-4** — `MAX_N**2` 케이스에 타임아웃 부여 또는 제거.
8. **Info** — `MAX_N` 값 고정 테스트 분리, 상한 근거 주석, 타입 힌트, `orca` 파일 삭제.

1~2번은 시그니처 변경이므로 테스트도 함께 수정해야 한다. 아직 미커밋 상태이니 지금이
가장 저렴한 시점이다.

---

## 부록 A. 이번 리뷰에서 실행한 검증

| 확인 항목 | 방법 | 결과 |
|---|---|---|
| 전체 통과 | `python -m pytest tests -q` | `29 passed in 0.09s` |
| H-1 | `pytest tests -q` | `ModuleNotFoundError: No module named 'src'` |
| H-2 (조기 바인딩) | `calc.MAX_N = 500` 후 `factorial(600)` | 통과 (1409자리) — 기본값은 `(1000,)` 고정 |
| M-3 (가드 무력화) | `factorial(n, MAX_N=10**9)`, n=3k/20k/50k | 0.001s / 0.075s / 0.558s — 초선형 증가 |
| M-4 (상한 미검증) | `factorial(5, -1)`, `(5, 0)`, `(5, 2.5)`, `(5, None)` | 모두 `n`을 탓하는 메시지 / `TypeError` |
| M-5 (문서 불일치) | README 39·45·46·146·158행 대조 | 시그니처·파라미터·테스트 개수 모두 불일치 |
| M-1 | 임의 스크립트에서 `from src.calc import factorial` | stdout에 `first calc` 선출력 |
| M-2 | 비정수 `n` 직접 호출 | 본문 표대로 예외 타입 분기 확인 |
| L-3 (해결 확인) | `MAX_N`을 999/1001로 변형 후 전체 테스트 | 양쪽 모두 `1 failed, 28 passed` — 검출됨 |
| L-4 | 상한 가드 제거 변종으로 전체 테스트 | 60초 타임아웃 미완료 (`rc=124`) |

## 부록 B. 재현 명령

```bash
# H-1 실패 재현
pytest tests -q

# 정상 통과
python -m pytest tests -q      # 29 passed

# H-2 재현
python -c "import sys; sys.path.insert(0,'.'); \
import src.calc as c; c.MAX_N = 500; print(len(str(c.factorial(600))))"
# -> 1409  (상한 500으로 낮췄는데 600이 통과)

# N-1 재현 (clean 상태에서)
python -m pytest tests -q && git status --porcelain
```

> 이 환경에서 `python`은 Microsoft Store 별칭 스텁으로 연결되어 아무것도 실행하지 않고
> 종료된다. 실제 인터프리터는 `C:/Users/young/anaconda3/python.exe`를 사용해야 한다.

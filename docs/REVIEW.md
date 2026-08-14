# 코드 리뷰 기록

이 문서는 `src/calc.py`와 `tests/test_calc.py`에 대한 리뷰를 누적 기록한다.
새 리뷰는 항상 문서 맨 아래에 `## 리뷰 #N` 형태로 추가하며, 기존 내용은 수정하지 않는다.

> 참고: 이 파일은 `8642a4e` (디렉토리 초기화)에서 삭제되었다가 이번 리뷰로 다시 만들어졌다.
> `34cfa34`에 있던 **리뷰 #1** 본문은 현재 워킹 트리에 없으므로
> (`git show 34cfa34:docs/REVIEW.md`로 열람 가능), 아래 **리뷰 #2**는 #1의 지적 사항을
> 요약해 인용하는 형태로 이어간다. 번호는 이력과의 연속성을 위해 #2부터 시작한다.

---

## 리뷰 #2

- **일시**: 2026-08-14
- **대상**: `conftest.py`, `src/calc.py`, `tests/test_calc.py` (모두 미추적 신규 파일)
- **기준 커밋**: `34cfa34` (factorial 기본 함수 생성) — 워킹 트리는 그 이후 미커밋 상태
- **테스트 결과**:
  - `python -m pytest -q` → **11 passed** (0.08s)
  - `pytest -q` (실행 파일 직접 호출) → **11 passed** (0.06s) ✅ 리뷰 #1의 High 이슈 해소
  - 환경: pytest 7.4.4 / CPython 3.12 (`C:\Users\young\anaconda3\python.exe`)

### 리뷰 범위에 대한 참고

작업 지시는 "커밋되지 않은 변경(`git diff`)"이었으나, **`git diff`와 `git diff --cached`는 모두 비어 있다.**
변경분은 전부 *미추적(untracked)* 파일 형태로 존재한다.

```
?? conftest.py
?? src/calc.py
?? tests/test_calc.py
?? __pycache__/conftest.cpython-312-pytest-7.4.4.pyc
?? src/__pycache__/calc.cpython-312.pyc
?? tests/__pycache__/test_calc.cpython-312-pytest-7.4.4.pyc
```

따라서 위 3개 소스 파일 전체를 리뷰 대상으로 삼았다.
`__pycache__/*.pyc`는 리뷰 중 테스트를 실행하면서 재생성된 것이므로 코드 변경분은 아니다
(다만 아래 M4 항목의 근거는 된다).

### 요약

`factorial` 구현은 **정확하다**. 반복문 기반이라 재귀 깊이 제한이 없고,
`result = 1` + `range(2, n + 1)` 조합이 `n=0`, `n=1`을 별도 분기 없이 처리한다.
`n=1000`까지 `math.factorial`과 결과가 일치함을 직접 확인했다.
테스트도 정상값·경계값·예외 경로를 고루 덮고 있으며 11개 전부 통과한다.

이번 변경의 핵심은 **루트 `conftest.py` 추가**이고, 이것이 리뷰 #1에서 High로 지적했던
`pytest` 단독 실행 시 수집 실패 문제를 실제로 해결했다. 동작 원리도 파일 주석 설명대로 맞다
— pytest의 `prepend` 임포트 모드가 루트 `conftest.py`를 임포트하면서 프로젝트 루트를
`sys.path`에 넣어주고, 그 덕분에 `from src.calc import factorial`이 해석된다.

**이번 리뷰에서 새로 발견한 correctness 이슈는 M2(부호에 따라 예외 종류가 달라지는 문제) 하나다.**
나머지는 리뷰 #1에서 이월된 항목이거나 패키징/설정 위생 문제이며, **High 등급은 없다.**

---

### 발견 사항

#### [Medium] M1. `conftest.py` 방식은 동작하지만 실행 위치에 취약하다

현재 방식은 pytest를 **프로젝트 루트에서** 실행할 때만 성립한다.
`tests/` 안에서 실행하면 rootdir가 `tests/`로 잡히고 루트 `conftest.py`가 수집되지 않아 즉시 깨진다.

실제 재현:

```
$ cd tests && pytest -q test_calc.py
test_calc.py:5: in <module>
    from src.calc import factorial
E   ModuleNotFoundError: No module named 'src'
!!!!!! Interrupted: 1 error during collection !!!!!!
```

또한 `--import-mode=importlib`를 쓰면 `sys.path` 주입이 일어나지 않아 같은 방식으로 깨진다.
IDE의 "이 테스트만 실행" 기능이 파일 디렉토리를 cwd로 잡는 경우에도 재현될 수 있다.

리뷰 #1의 지적이 완전히 사라진 게 아니라 **재현 조건이 좁아진 상태**로 보는 게 정확하다.
설정 파일로 못을 박아두면 실행 위치와 무관해진다:

```toml
# pyproject.toml (또는 pytest.ini)
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

ini 파일이 있으면 rootdir가 고정되므로 서브디렉토리 실행 문제까지 함께 해결된다.
이 경우 `conftest.py`는 없어도 되지만, 남겨둬도 무해하다.

#### [Medium] M2. 비정수 입력에서 **부호에 따라 예외 종류가 달라진다** (신규)

리뷰 #1은 `factorial(2.5)` → `TypeError`만 확인했다. 음수 쪽을 확인해 보면 계약이 갈라진다:

| 입력 | 결과 |
|---|---|
| `2.5` | `TypeError: 'float' object cannot be interpreted as an integer` |
| `-2.5` | **`ValueError: n must be non-negative`** |
| `3.0` | `TypeError: ...` |
| `True` | `1` (정상 반환, 반환 타입 `int`) |
| `"3"` | `TypeError: '<' not supported between 'str' and 'int'` |
| `None` | `TypeError: '<' not supported between 'NoneType' and 'int'` |

`factorial(-2.5)`의 실제 문제는 **타입**이지 부호가 아닌데, `"n must be non-negative"`라는
부호에 대한 메시지가 나간다. 호출자가 `-2.5`를 `2.5`로 고쳐도 이번엔 `TypeError`가 나므로
메시지를 따라가면 오진하게 된다. 같은 `float` 타입인데 부호에 따라 예외 클래스가 갈리는 것도
`except` 절을 작성하는 쪽에서 다루기 어렵다.

`n < 0` 검사보다 **앞에** 타입 검증을 두면 세 가지가 한 번에 정리된다
(`-2.5` 오진, `range()`에서 새어 나오는 내부 메시지, `bool` 통과):

```python
if isinstance(n, bool) or not isinstance(n, int):
    raise TypeError(f"n must be an int, got {type(n).__name__}")
if n < 0:
    raise ValueError("n must be non-negative")
```

> `bool` 처리와 stdlib 정합성은 판단이 필요하다 — 아래 **판단 필요 J1** 참고.

#### [Medium] M3. 타입 힌트 부재 (리뷰 #1 #2에서 이월)

`def factorial(n):`에 시그니처 정보가 없다. 정수 전용 함수임을 명시하면
IDE 자동완성과 mypy 등 정적 분석에서 이득이 있고, M2의 계약도 코드로 드러난다.

```python
def factorial(n: int) -> int:
```

#### [Medium] M4. `.gitignore` 부재 — 이번 커밋에서 `.pyc`가 다시 딸려 들어갈 위치다

리뷰 #1에서 Low로 분류했으나, **지금은 실제 발생 직전 상태**라 등급을 올린다.

- 저장소에 `.gitignore`가 없다.
- `src/`와 `tests/`가 통째로 미추적 상태다. `git add src tests` 또는 `git add -A`를 하면
  `src/__pycache__/calc.cpython-312.pyc` 등이 **함께 스테이징된다.**
- 이건 가정이 아니라 전례가 있다. `34cfa34` 커밋에는 실제로
  `src/__pycache__/calc.cpython-312.pyc`와
  `tests/__pycache__/test_calc.cpython-312-pytest-7.4.4.pyc`가 포함되어 있다.

커밋 전에 최소한 다음을 추가할 것을 권한다:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
```

(`.pytest_cache/`는 pytest가 자체 `.gitignore`를 넣어줘서 지금은 가려져 있지만,
명시해 두는 편이 안전하다.)

#### [Medium] M5. 프로젝트 메타데이터 부재

`pyproject.toml`, `requirements.txt`, `setup.cfg` 어느 것도 없다.

- 테스트가 `pytest`에 의존하는데 그 의존성이 어디에도 선언되어 있지 않다.
  새 개발자나 CI는 `pytest` 설치 필요 여부를 코드만 보고 알 수 없다.
- pytest 설정을 둘 곳이 없어 M1의 `pythonpath` 해법도 적용할 자리가 없다.

M1과 함께 `pyproject.toml` 하나로 해결된다.

#### [Low] L1. `src`가 최상위 임포트 이름으로 노출된다

`src/__init__.py`가 없어 `src`는 PEP 420 암묵적 네임스페이스 패키지로 잡힌다
(확인: `src.__file__` is `None`, `src.__path__` = `_NamespacePath([...])`).

동작에는 문제가 없지만 `src`는 이름이 지나치게 일반적이라,
같은 환경에 `src`를 노출하는 다른 프로젝트가 있으면 충돌하거나
엉뚱한 쪽이 임포트될 수 있다. 정식 패키지로 갈 거라면 `calc` 같은
고유한 패키지명 + `src/` 레이아웃 조합이 안전하다.

> 정식 패키지화 여부는 판단이 필요하다 — 아래 **판단 필요 J2** 참고.

#### [Low] L2. 독스트링 형식 (리뷰 #1 #4에서 이월)

동작 설명은 충분하나 `Args` / `Returns` / `Raises` 절이 없다.
`Raises: ValueError` 정보가 본문 문장에만 있어 자동 문서화 도구가 인식하지 못한다.
doctest 예시(`>>> factorial(5)` → `120`)를 넣으면 문서와 테스트를 함께 얻는다.
M2를 반영한다면 `Raises: TypeError`도 함께 명시해야 한다.

---

### 테스트 코드 평가

**좋은 점** (리뷰 #1 평가 유지)

- `test_factorial_zero_and_one` — 경계값(0, 1)을 정확히 짚었다.
- `test_factorial_matches_math_factorial` — `math.factorial`을 오라클로 삼은
  파라미터화 테스트는 하드코딩 기댓값보다 견고하다.
- `pytest.raises(ValueError, match="non-negative")` — 예외 타입뿐 아니라
  메시지까지 검증해 정확도가 높다.
- 음수 케이스를 `-1` 단독과 `[-2, -10, -1000]` 파라미터화로 나눠 덮었다.

**보완 제안**

| # | 내용 | 심각도 |
|---|---|---|
| T1 | 비정수 입력(`2.5`, `-2.5`, `True`, `None`, `"5"`) 테스트가 없다. M2의 계약을 확정한 뒤 그에 맞춰 추가할 것. 특히 `-2.5`는 현재 조용히 `ValueError`로 통과해 버리는 경로다. | Medium |
| T2 | 반환 타입 검증(`assert isinstance(factorial(5), int)`)이 없다. `bool` 입력 문제와 연결된다. | Low |
| T3 | 큰 입력(`n=1000` 등) 테스트가 없다. 리뷰 중 수동 확인 결과 `math.factorial(1000)`과 일치했으나, 회귀 방지용으로 테스트에 넣어둘 가치가 있다. | Low |
| T4 | `conftest.py`가 추가된 만큼, `pytest`/`python -m pytest` 양쪽 실행 경로를 CI에서 함께 돌려 M1의 회귀를 잡는 것을 권한다. | Low |

---

### 판단이 필요한 사항 (사람 결정)

아래는 리뷰어가 임의로 정할 수 없는, **의도·방향성에 대한 결정**이다.
각 항목의 결론에 따라 위 findings의 처리 방식이 달라진다.

#### J1. 비정수·`bool` 입력의 계약을 무엇으로 할 것인가

- **선택지 A — stdlib 정합**: `float`에 `TypeError`를 내는 현 동작은 `math.factorial`과 동일하다.
  "stdlib과 같은 계약을 따른다"고 정하면 M2는 **메시지 개선만** 하면 된다
  (`-2.5`의 오진 메시지는 여전히 고쳐야 한다).
- **선택지 B — 명시적 검증**: `bool` 포함해 `int`가 아니면 전부 `TypeError`.
  `factorial(True) == 1`이 조용히 통과하는 경로가 막힌다. 단, `math.factorial(True)`도 `1`을
  반환하므로 stdlib과는 어긋난다.
- 관련 findings: **M2, M3, L2, T1, T2**

#### J2. 이 저장소를 정식 패키지로 만들 것인가, 학습용 스크립트로 둘 것인가

- 정식 패키지화(`pyproject.toml` + 고유 패키지명 + `pip install -e .`)를 하면
  **M1, M5, L1이 한꺼번에 해소**된다. 대신 구조가 무거워진다.
- 학습/실습용으로 유지한다면 `pyproject.toml`에 `[tool.pytest.ini_options]`만 넣는
  최소 조치로 M1·M5만 처리하고 L1은 수용(WONTFIX)해도 된다.
- 관련 findings: **M1, M5, L1**

#### J3. `math.factorial` 대신 자체 구현을 유지할 것인가

기능적으로 `math.factorial`과 동일하다. 실습·학습 목적의 재구현이라면 문제없고,
프로덕션 코드라면 stdlib이 더 빠르고 안전하다.
저장소 이력(`orca_test`, 실습 커밋)상 학습 맥락으로 보여 리뷰어는 **변경 불필요**로 판단했으나,
확정은 필요하다.

#### J4. 삭제된 `README.md` / `docs/REVIEW.md` 누적 규약을 복원할 것인가

`8642a4e` (디렉토리 초기화)에서 `README.md`(119줄)와 `docs/REVIEW.md`(132줄)가 함께 삭제됐다.
이번 리뷰로 `docs/REVIEW.md`만 재생성했다.

- 삭제가 **의도된 리셋**이었다면, 이 문서를 리뷰 #2가 아니라 리뷰 #1로 다시 번호 매기고
  위 헤더의 이력 참고 문구를 지우는 게 맞다.
- 삭제가 **사고**였다면 `README.md`도 `git show 34cfa34:README.md`로 복원해야 한다.
- 리뷰어는 이력 연속성을 보존하는 쪽(#2로 이어쓰기)을 택했으나, 되돌리기 쉬운 결정이다.

#### J5. 이번 변경의 커밋 단위와 `.pyc` 포함 여부

M4에서 지적했듯 지금 `git add -A`를 하면 `.pyc` 3개가 함께 들어간다.
`.gitignore`를 **먼저** 커밋할지, 아니면 이번 커밋에서 경로를 지정해 소스 3개만 담을지
(`git add conftest.py src/calc.py tests/test_calc.py`) 결정이 필요하다.
리뷰어는 코드를 수정하지 않는 범위였으므로 `.gitignore`를 생성하지 않았다.

---

### 조치 우선순위

| 순위 | 항목 | 심각도 | 선행 결정 |
|---|---|---|---|
| 1 | `.gitignore` 추가 후 커밋 — `.pyc` 재유입 차단 | Medium | J5 |
| 2 | `pyproject.toml`에 `pythonpath`/`testpaths` 설정 (M1 + M5) | Medium | J2 |
| 3 | 비정수 입력 계약 확정 + 타입 검증 추가 (M2) | Medium | J1 |
| 4 | 타입 힌트 추가 (M3) | Medium | J1 |
| 5 | 비정수/반환타입/큰 입력 테스트 보강 (T1–T3) | Medium~Low | J1 |
| 6 | 독스트링 정비 (L2), `src` 패키지명 재검토 (L1) | Low | J1, J2 |

### 리뷰 결론

**머지 차단 사유 없음.** 구현은 정확하고 테스트는 전부 통과하며,
이번 변경(`conftest.py`)은 리뷰 #1의 최우선 이슈를 실제로 해결했다.
다만 **커밋 전에 `.gitignore`만은 처리할 것**을 권한다(M4/J5) — 이력상 이미 한 번 발생한 문제다.
나머지는 후속 커밋으로 미뤄도 무방하다.

---

## 리뷰 #3

- **일시**: 2026-08-14
- **대상**: `.gitignore`(신규), `pyproject.toml`(신규), `src/calc.py`, `tests/test_calc.py` (모두 미추적)
- **기준**: 리뷰 #2 이후 워킹 트리 변경분
- **테스트 결과**: 아래 5개 실행 경로 **전부 11 passed** (pytest 7.4.4 / CPython 3.12)

### 이번 변경 요약

리뷰 #2의 지적이 반영되었다. 워킹 트리 구성이 바뀌었다:

| 파일 | 상태 |
|---|---|
| `conftest.py` | **삭제됨** → `pyproject.toml`로 대체 |
| `pyproject.toml` | **신규** — `[tool.pytest.ini_options]`에 `pythonpath`, `testpaths` |
| `.gitignore` | **신규** — `__pycache__/`, `*.py[cod]`, `.pytest_cache/` |
| `src/calc.py` | **변경 없음** (리뷰 #2 시점과 바이트 동일) |
| `tests/test_calc.py` | **변경 없음** (리뷰 #2 시점과 바이트 동일) |

`git diff`는 이번에도 비어 있다 — 변경분은 전부 미추적 파일이다.

### 해소 확인 (실행으로 검증)

#### ✅ M1 해소 — 실행 위치·임포트 모드 무관하게 동작

`pyproject.toml`의 주석이 주장하는 두 가지(하위 디렉토리 실행, `--import-mode=importlib`)를
모두 실제로 돌려 확인했고, **주장은 정확하다**:

| # | 실행 방법 | 결과 |
|---|---|---|
| 1 | `python -m pytest -q` (루트) | 11 passed |
| 2 | `pytest -q` (루트) | 11 passed |
| 3 | `pytest` 인자 없이 (`testpaths` 경유) | 11 passed — `tests\test_calc.py` 수집 |
| 4 | `cd tests && pytest -q test_calc.py` | **11 passed** ← 리뷰 #2에서 깨지던 경로 |
| 5 | `pytest -q --import-mode=importlib` | **11 passed** ← 리뷰 #2에서 우려하던 경로 |

`pyproject.toml`에 `[tool.pytest.ini_options]`가 있으면 그 파일이 inifile로 인식되어
rootdir가 프로젝트 루트로 고정되고, `pythonpath`는 cwd가 아닌 **rootdir 기준**으로 해석된다.
그래서 4번이 통과한다. `conftest.py`를 지운 것도 타당하다 — 이제 불필요하다.

#### ✅ M4 해소 — `.gitignore`가 실제로 동작

```
$ git check-ignore -v src/__pycache__/calc.cpython-312.pyc ...
.gitignore:1:__pycache__/     src/__pycache__/calc.cpython-312.pyc
.gitignore:1:__pycache__/     tests/__pycache__/test_calc.cpython-312-pytest-7.4.4.pyc
.gitignore:3:.pytest_cache/   .pytest_cache/CACHEDIR.TAG
.gitignore:3:.pytest_cache/   tests/.pytest_cache/CACHEDIR.TAG
```

패턴에 선행 슬래시가 없어 하위 경로에서도 매칭된다.
`git add -A` 시뮬레이션 결과 **소스 5개만 스테이징되고 아티팩트는 하나도 들어가지 않는다**:

```
$ git add -An
add '.gitignore'
add 'docs/REVIEW.md'
add 'pyproject.toml'
add 'src/calc.py'
add 'tests/test_calc.py'
```

리뷰 #2에서 최우선(1순위)으로 올렸던 `.pyc` 재유입 위험은 사라졌다. **J5도 함께 해소된다.**

#### ⚠️ M5 부분 해소에 그침 — 아래 N1 참고

### 신규 발견 사항

#### [Medium] N1. `pyproject.toml`에 `[project]`/`[build-system]`이 없어 의존성이 여전히 미선언

파싱해 보면 최상위 테이블이 `tool` 하나뿐이다:

```
top-level tables: ['tool']
has [project]: False | has [build-system]: False
```

M5는 두 가지를 지적했는데 그중 하나만 해결됐다:

- ✅ pytest 설정을 둘 자리가 생겼다 (M1 해법 적용 완료)
- ❌ **`pytest` 의존성은 여전히 어디에도 선언되어 있지 않다.**
  새 개발자나 CI는 무엇을 설치해야 하는지 코드만 보고 알 수 없다.
  `requirements-dev.txt`도 없다.

설정 전용 `pyproject.toml`로서 문법상 문제는 없고 pytest는 정상 동작하지만,
`pip install .` / `pip install -e .`는 `[build-system]`이 없어 실패한다.
최소 조치는 다음 중 하나다:

```toml
# 최소안 — 설치는 안 하고 의존성만 기록
[dependency-groups]
dev = ["pytest>=7.0"]
```

```toml
# 정식안 — J2에서 패키지화를 택할 경우
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "..."
version = "0.1.0"
[dependency-groups]
dev = ["pytest>=7.0"]
```

> `pythonpath` ini 옵션은 pytest 7.0부터 내장이라 별도 플러그인이 필요 없다.
> 현재 환경(7.4.4)에서는 문제없으나, 의존성을 선언한다면 `pytest>=7.0` 하한을 명시할 것.

#### [Low] N2. `.gitignore` 커버리지는 현 구조 기준으로만 충분하다

지금 있는 3줄은 현재 생성되는 아티팩트를 전부 덮는다.
다만 J2에서 패키지화를 택하면 `*.egg-info/`, `build/`, `dist/`가, 가상환경을 쓰면 `.venv/`가
추가로 필요해진다. **지금 조치할 필요는 없고**, J2 결정 시 함께 처리하면 된다.

### 미해소 이월 항목 (코드 무변경)

`src/calc.py`와 `tests/test_calc.py`가 리뷰 #2 시점과 **바이트 단위로 동일**하므로,
코드 관련 지적은 전부 그대로 남아 있다. 재확인 결과도 동일하다:

```
signature: (n)          ← 타입 힌트 없음 (M3)
2.5  -> TypeError  'float' object cannot be interpreted as an integer
-2.5 -> ValueError n must be non-negative      ← 부호에 따라 예외가 갈림 (M2)
True -> 1                                       ← bool 통과 (M2)
```

| 항목 | 심각도 | 상태 |
|---|---|---|
| M2 — 비정수 입력에서 부호에 따라 예외 종류가 달라짐 | Medium | **미해소** |
| M3 — 타입 힌트 부재 | Medium | **미해소** |
| L1 — `src`가 최상위 네임스페이스 패키지로 노출 | Low | **미해소** (J2 종속) |
| L2 — 독스트링 `Args`/`Returns`/`Raises` 절 부재 | Low | **미해소** |
| T1 — 비정수 입력 테스트 부재 | Medium | **미해소** |
| T2 — 반환 타입 검증 부재 | Low | **미해소** |
| T3 — 큰 입력 테스트 부재 | Low | **미해소** |
| T4 — CI에서 복수 실행 경로 검증 | Low | 부분 — 설정으로 견고해졌으나 CI 자체가 없음 |

이 항목들은 **J1(비정수·`bool` 계약)** 결정 없이는 손댈 수 없다.
지금까지 반영된 것은 전부 J1·J2 결정이 필요 없는 인프라 항목뿐이다.

### 판단이 필요한 사항 (사람 결정) — 갱신

| 항목 | 내용 | 상태 |
|---|---|---|
| **J1** | 비정수·`bool` 입력 계약 (stdlib 정합 vs 명시적 `TypeError`) | **미결 — 현재 최대 병목.** M2·M3·L2·T1·T2가 전부 여기 묶여 있다 |
| **J2** | 정식 패키지화 vs 학습용 스크립트 유지 | **부분 진행.** `pyproject.toml`이 생겼으나 설정 전용이라 방향은 아직 미확정. N1·N2·L1이 종속 |
| **J3** | `math.factorial` 대신 자체 구현 유지 여부 | 미결 (리뷰어 판단은 여전히 "변경 불필요") |
| **J4** | 삭제된 `README.md` 복원 및 리뷰 번호 규약 | 미결. 이 문서는 #2에 이어 #3으로 계속 이어썼다 |
| **J5** | 커밋 단위와 `.pyc` 포함 여부 | ✅ **해소** — `.gitignore`로 `git add -A`가 안전해졌다 |

J4 관련 참고: `README.md`는 여전히 없다. `git show 34cfa34:README.md`로 복원 가능하다.

### 조치 우선순위 (갱신)

| 순위 | 항목 | 심각도 | 선행 결정 |
|---|---|---|---|
| 1 | **J1 결정** — 이것이 풀려야 M2/M3/L2/T1/T2가 전부 움직인다 | — | — |
| 2 | 비정수 입력 계약 구현 + 타입 힌트 (M2, M3) | Medium | J1 |
| 3 | `pytest` 의존성 선언 (N1) | Medium | J2 |
| 4 | 비정수/반환타입/큰 입력 테스트 보강 (T1–T3) | Medium~Low | J1 |
| 5 | 독스트링 정비 (L2), `src` 패키지명 (L1), `.gitignore` 확장 (N2) | Low | J1, J2 |

### 리뷰 결론

**머지 차단 사유 없음.** 11개 테스트가 5가지 실행 경로 전부에서 통과하고,
리뷰 #2에서 1순위로 올렸던 `.gitignore` 이슈(M4/J5)와 M1이 **실행 검증 기준으로 해소됐다.**
`conftest.py`를 지우고 `pyproject.toml`로 옮긴 판단도 옳다.

이번 라운드는 **인프라 항목만 정리됐고 코드는 한 줄도 바뀌지 않았다.**
남은 항목은 대부분 **J1(비정수·`bool` 계약) 결정에 막혀 있으므로**,
다음 작업 전에 J1을 먼저 확정할 것을 권한다.
새로 추가된 이슈는 N1(의존성 미선언) 하나이며 Medium이다.

> 리뷰어 주: `tests/.pytest_cache/`는 리뷰어가 4번 실행 경로를 검증하며 생성한 것이다.
> `.gitignore`에 걸려 커밋되지 않으므로 무해하며, 작성자 쪽 문제가 아니다.

---

## 결정 기록 및 반영 (2026-08-14)

리뷰 #3이 "최대 병목"으로 지목한 판단 항목이 사람 결정으로 확정되어, 그에 막혀 있던
코드 항목을 일괄 반영했다. (이 절은 리뷰가 아니라 **작성자 측 대응 기록**이다.)

### 확정된 판단 항목

| 항목 | 결정 | 근거 |
|---|---|---|
| **J1** | **선택지 A — stdlib 정합** | `math.factorial`과 동일한 계약. `int`가 아니면 부호와 무관하게 `TypeError`, 음수 `int`만 `ValueError`. `bool`은 `int` 서브클래스이므로 통과시킨다 |
| **J2** | **학습용 유지** | `pyproject.toml`에 개발 의존성만 선언. 정식 패키지화는 하지 않음 |
| **J3** | **자체 구현 유지** | 리뷰어 판단대로 변경 불필요 (학습 목적) |
| **J4** | **README.md 복원 안 함** | `8642a4e`의 삭제를 의도된 리셋으로 본다. 필요 시 `git show 34cfa34:README.md`로 언제든 복원 가능 |
| **J5** | 해소됨 (리뷰 #3) | — |

### 반영 내역

| 항목 | 심각도 | 상태 | 내용 |
|---|---|---|---|
| M2 | Medium | ✅ 해소 | 타입 검증을 부호 검증 **앞**으로 이동. `factorial(-2.5)`가 이제 `TypeError: n must be an int, got float` |
| M3 | Medium | ✅ 해소 | `def factorial(n: int) -> int:` |
| N1 | Medium | ✅ 해소 | `[dependency-groups] dev = ["pytest>=7.0"]` — `pythonpath` ini 옵션이 7.0부터 내장이라 하한 명시 |
| T1 | Medium | ✅ 해소 | 비정수 6종(`2.5`, `3.0`, `"3"`, `None`, `[]`, `object()`) + `-2.5` 전용 회귀 테스트 추가 |
| T2 | Low | ✅ 해소 | `isinstance(factorial(5), int)` 및 `bool` 계약 테스트 추가 |
| T3 | Low | ✅ 해소 | `n=100`, `n=1000`을 `math.factorial`과 대조 |
| L2 | Low | ✅ 해소 | `Args`/`Returns`/`Raises`/`Examples` 절 추가. 예제는 `--doctest-modules`로 **실제 실행·검증**된다 |
| L1 | Low | ⛔ WONTFIX | J2(학습용 유지) 결정에 따라 `src` 네임스페이스 패키지를 수용 |
| N2 | Low | ⛔ 불필요 | J2에 따라 `*.egg-info/`·`build/`·`dist/`가 생기지 않음 |
| T4 | Low | ⚠️ **미해소** | CI 설정 파일은 추가하지 않았다. 아래 참고 |

### 계약 실동작 (확인 결과)

```
     2.5 -> TypeError: n must be an int, got float
    -2.5 -> TypeError: n must be an int, got float   ← M2 해소 지점
     3.0 -> TypeError: n must be an int, got float
     '3' -> TypeError: n must be an int, got str
    None -> TypeError: n must be an int, got NoneType
    True -> 1        (stdlib 정합, J1-A)
      -1 -> ValueError: n must be non-negative
       0 -> 1
       5 -> 120
```

### 테스트

11개 → **25개** (테스트 24 + doctest 1). 리뷰 #3의 5가지 실행 경로 전부 통과:

| # | 실행 방법 | 결과 |
|---|---|---|
| 1 | `python -m pytest -q` (루트) | 25 passed |
| 2 | `pytest -q` (루트) | 25 passed |
| 3 | `pytest` 인자 없이 | 25 passed |
| 4 | `cd tests && pytest -q test_calc.py` | 24 passed (해당 파일만 지정 → doctest 미수집) |
| 5 | `pytest -q --import-mode=importlib` | 25 passed |

doctest가 형식만 갖춘 게 아니라 실제로 동작함을 음성 대조로 확인했다 —
기대 출력을 `120` → `999`로 바꾸자 `1 failed`가 났고, 이후 원복했다.
수집 식별자는 `src/calc.py::calc.factorial`이다.

### 남은 항목 — T4 (Low)

`.github/workflows` 등 CI 설정은 **추가하지 않았다.** 리뷰의 T4 취지(복수 실행 경로를
CI에서 함께 돌려 M1 회귀를 잡을 것)는 타당하나, 다음 이유로 별도 결정 사항으로 남긴다.

- 이 저장소는 J2에서 **학습용 유지**로 확정됐고, 현재 브랜치는 아직 커밋도 푸시도 되지 않았다.
- CI 도입은 실행 환경·트리거·러너 선택 등 리뷰 범위 밖의 결정을 동반한다.

M1 회귀 위험 자체는 `pyproject.toml`의 `pythonpath`/`testpaths` 고정으로 이미 크게 줄었고,
위 5가지 경로를 수동 검증해 대체했다. CI가 필요하다면 별도 작업으로 진행할 것을 권한다.

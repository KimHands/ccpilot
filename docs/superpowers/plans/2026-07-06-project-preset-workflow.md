# 프로젝트 프리셋 & 단계별 워크플로우 — 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 새 프로젝트 시작 시 프리셋으로 플러그인을 활성화하고, 그 조합에 맞는 단계별 플레이북을 생성하는 사용자 레벨 슬래시 명령 시스템을 만든다.

**Architecture:** 순수 파이썬 패키지 `pw/`가 결정적 로직(프리셋 로드·슬러그 검증·설정 병합·플레이북 생성·상태 관리)을 담당하고, 얇은 슬래시 명령 md가 이를 호출한다. 단일 원천은 `presets.json`. 설치는 `install.sh`가 `~/.claude/`로 복사한다.

**Tech Stack:** Python 3.10+ (표준 라이브러리만), pytest, 마크다운 슬래시 명령, JSON 데이터.

## Global Constraints

- Python 3.10+ 표준 라이브러리만 사용 — 외부 의존성 금지.
- 슬러그는 반드시 `plugin@marketplace` 정확 형식. 기록 전 `~/.claude/plugins/installed_plugins.json`과 대조.
- 파일 쓰기는 **비파괴**: 기존 JSON 키·마커 밖 텍스트 보존. 생성 블록은 `<!-- pw:begin ... -->` … `<!-- pw:end -->` 마커로만 교체.
- 상시 활성(alwaysOn): `superpowers@superpowers-dev`, `agentmemory@agentmemory`, `andrej-karpathy-skills@karpathy-skills`.
- 단계 순서: `brainstorm → plan → implement → review → ship`.
- 모든 명령은 실행 전 설치 목록과 상태를 검증하고, `--dry-run`이면 파일을 바꾸지 않는다.
- 스키마 버전 = 1 (presets.json, project-state.json 모두).

---

### Task 1: 저장소 스캐폴딩 + presets.json + 로드

**Files:**
- Create: `pw/__init__.py` (빈 파일)
- Create: `pw/data.py`
- Create: `pw/presets.json`
- Test: `tests/test_data_load.py`

**Interfaces:**
- Produces: `pw.data.load_presets(path: str) -> dict` — presets.json을 읽어 `schemaVersion==1` 검증 후 dict 반환. 키 누락/버전 불일치 시 `ValueError`.

- [ ] **Step 1: presets.json 작성**

Create `pw/presets.json`:

```json
{
  "schemaVersion": 1,
  "alwaysOn": ["superpowers@superpowers-dev", "agentmemory@agentmemory", "andrej-karpathy-skills@karpathy-skills"],
  "phaseModel": {
    "phases": ["brainstorm", "plan", "implement", "review", "ship"],
    "roles": {
      "brainstorm": [
        {"role": "요구사항 취조", "tool": "grill-me", "optional": true},
        {"role": "설계 확정", "tool": "superpowers:brainstorming"},
        {"role": "기존코드 이해", "tool": "understand-anything", "whenCapability": "existing-code"}
      ],
      "plan": [
        {"role": "계획 작성", "tool": "superpowers:writing-plans"},
        {"role": "영향 분석", "tool": "understand-anything", "whenCapability": "existing-code"},
        {"role": "라이브러리 문서", "tool": "context7"}
      ],
      "implement": [
        {"role": "구현 루프", "tool": "superpowers:test-driven-development"},
        {"role": "언어 인텔리전스", "tool": "__lsp_by_language__"},
        {"role": "테스트 작성/수정", "tool": "test-writer-fixer"},
        {"role": "라이브러리 문서", "tool": "context7"},
        {"role": "UI 생성", "tool": "frontend-design", "whenCapability": "frontend"},
        {"role": "문서 산출물", "tool": "document-skills", "whenCapability": "docs-output"}
      ],
      "review": [
        {"role": "주력 리뷰", "tool": "/code-review"},
        {"role": "단순화", "tool": "code-simplifier"},
        {"role": "실시간 보안", "tool": "security-guidance"},
        {"role": "정적 보안", "tool": "static-analysis"},
        {"role": "한국 규제", "tool": "kesekit", "whenCapability": "kr-compliance"}
      ],
      "ship": [
        {"role": "커밋/PR", "tool": "gh"},
        {"role": "릴리스 문서", "tool": "document-skills", "whenCapability": "docs-output"},
        {"role": "학습 영속", "tool": "agentmemory:remember"}
      ]
    }
  },
  "capabilityTags": {
    "detect": {
      "typescript": ["package.json", "tsconfig.json"],
      "python": ["pyproject.toml", "requirements.txt"],
      "go": ["go.mod"],
      "rust": ["Cargo.toml"],
      "frontend": ["package.json::react", "package.json::next"],
      "infra": ["Dockerfile", "*.tf"]
    },
    "lspFor": {
      "typescript": "typescript-lsp@claude-plugins-official",
      "python": "pyright-lsp@claude-plugins-official",
      "go": "gopls-lsp@claude-plugins-official",
      "rust": "rust-analyzer-lsp@claude-plugins-official"
    }
  },
  "presets": {
    "web-fullstack": {"plugins": ["typescript-lsp@claude-plugins-official", "pyright-lsp@claude-plugins-official", "frontend-design@claude-plugins-official", "figma@claude-plugins-official", "vercel@claude-plugins-official", "context7@claude-plugins-official", "test-writer-fixer@awesome-claude-plugins", "code-simplifier@claude-plugins-official", "security-guidance@claude-plugins-official", "understand-anything@understand-anything"]},
    "backend-api": {"plugins": ["context7@claude-plugins-official", "test-writer-fixer@awesome-claude-plugins", "static-analysis@trailofbits", "security-guidance@claude-plugins-official", "code-simplifier@claude-plugins-official", "understand-anything@understand-anything"], "lspByLanguage": true},
    "security-audit": {"plugins": ["static-analysis@trailofbits", "kesekit@kesekit", "security-guidance@claude-plugins-official", "understand-anything@understand-anything", "code-simplifier@claude-plugins-official"], "capabilities": ["kr-compliance"]},
    "docs-deck": {"plugins": ["document-skills@anthropic-agent-skills", "felo-slides@felo-ai", "context7@claude-plugins-official"], "personalSkills": ["academic-pptx", "pptx-from-layouts"], "capabilities": ["docs-output"]},
    "minimal": {"plugins": ["context7@claude-plugins-official"], "lspByLanguage": true}
  },
  "invocationRules": {
    "orchestrator": {"primary": "superpowers", "rescueOnly": ["codex"]},
    "memory": {"single": "agentmemory"},
    "review": {"primary": "/code-review", "specialists": ["code-simplifier", "security-guidance", "static-analysis", "kesekit"], "order": "primary first then specialists on explicit trigger", "stopWhen": "no new findings"},
    "lsp": "one per detected language",
    "docs": {"general": "document-skills", "specialized": ["academic-pptx", "pptx-from-layouts", "felo-slides"]}
  }
}
```

- [ ] **Step 2: 실패 테스트 작성**

Create `tests/test_data_load.py`:

```python
import json, os, pytest
from pw import data

PRESETS = os.path.join(os.path.dirname(__file__), "..", "pw", "presets.json")

def test_load_presets_returns_dict_with_required_keys():
    d = data.load_presets(PRESETS)
    assert d["schemaVersion"] == 1
    for key in ("alwaysOn", "phaseModel", "capabilityTags", "presets", "invocationRules"):
        assert key in d
    assert d["phaseModel"]["phases"] == ["brainstorm", "plan", "implement", "review", "ship"]

def test_load_presets_rejects_wrong_schema(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"schemaVersion": 99}))
    with pytest.raises(ValueError):
        data.load_presets(str(p))
```

- [ ] **Step 3: 실패 확인**

Run: `python3 -m pytest tests/test_data_load.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pw'` 또는 `AttributeError: load_presets`.

- [ ] **Step 4: 최소 구현**

Create `pw/__init__.py` (빈 파일). Create `pw/data.py`:

```python
import json

REQUIRED_KEYS = ("alwaysOn", "phaseModel", "capabilityTags", "presets", "invocationRules")

def load_presets(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("schemaVersion") != 1:
        raise ValueError(f"unsupported schemaVersion: {d.get('schemaVersion')}")
    for k in REQUIRED_KEYS:
        if k not in d:
            raise ValueError(f"missing key: {k}")
    return d
```

- [ ] **Step 5: 통과 확인**

Run: `python3 -m pytest tests/test_data_load.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: 커밋**

```bash
git add pw/__init__.py pw/data.py pw/presets.json tests/test_data_load.py
git commit -m "feat: presets.json data source + load_presets"
```

---

### Task 2: 설치 플러그인 읽기 + 슬러그 검증

**Files:**
- Modify: `pw/data.py`
- Test: `tests/test_data_validate.py`

**Interfaces:**
- Consumes: `pw.data.load_presets`
- Produces:
  - `pw.data.installed_plugins(installed_json_path: str) -> set[str]` — `installed_plugins.json`의 `plugins` 키 집합 반환.
  - `pw.data.validate_slugs(slugs: list[str], installed: set[str]) -> tuple[list[str], list[str]]` — `(valid, missing)` 반환, 입력 순서 보존.

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_data_validate.py`:

```python
import json
from pw import data

def test_installed_plugins_reads_keys(tmp_path):
    p = tmp_path / "installed.json"
    p.write_text(json.dumps({"plugins": {"a@m1": [{}], "b@m2": [{}]}}))
    assert data.installed_plugins(str(p)) == {"a@m1", "b@m2"}

def test_validate_slugs_splits_valid_and_missing():
    installed = {"context7@claude-plugins-official", "kesekit@kesekit"}
    valid, missing = data.validate_slugs(
        ["context7@claude-plugins-official", "ghost@nowhere", "kesekit@kesekit"], installed)
    assert valid == ["context7@claude-plugins-official", "kesekit@kesekit"]
    assert missing == ["ghost@nowhere"]
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m pytest tests/test_data_validate.py -v`
Expected: FAIL — `AttributeError: installed_plugins`.

- [ ] **Step 3: 최소 구현** — `pw/data.py`에 추가:

```python
def installed_plugins(installed_json_path):
    with open(installed_json_path, encoding="utf-8") as f:
        d = json.load(f)
    return set(d.get("plugins", {}).keys())

def validate_slugs(slugs, installed):
    valid = [s for s in slugs if s in installed]
    missing = [s for s in slugs if s not in installed]
    return valid, missing
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m pytest tests/test_data_validate.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw/data.py tests/test_data_validate.py
git commit -m "feat: installed_plugins + validate_slugs"
```

---

### Task 3: JSON 읽기/쓰기 + 마커 블록 upsert

**Files:**
- Create: `pw/fsutil.py`
- Test: `tests/test_fsutil_marker.py`

**Interfaces:**
- Produces:
  - `pw.fsutil.read_json(path: str, default=None) -> dict` — 없으면 default.
  - `pw.fsutil.write_json(path: str, obj: dict) -> None` — 부모 폴더 생성, 2-space indent, `ensure_ascii=False`.
  - `pw.fsutil.upsert_marker_block(text: str, block: str, begin: str, end: str) -> str` — `begin`~`end` 사이를 `block`으로 교체. 마커 없으면 끝에 `\n{begin}\n{block}\n{end}\n` append. 마커 밖 텍스트 보존.

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_fsutil_marker.py`:

```python
from pw import fsutil

BEGIN, END = "<!-- pw:begin -->", "<!-- pw:end -->"

def test_upsert_appends_when_no_marker():
    out = fsutil.upsert_marker_block("existing content\n", "NEW", BEGIN, END)
    assert "existing content" in out
    assert f"{BEGIN}\nNEW\n{END}" in out

def test_upsert_replaces_between_markers_preserving_outside():
    text = f"top\n{BEGIN}\nOLD\n{END}\nbottom\n"
    out = fsutil.upsert_marker_block(text, "NEW", BEGIN, END)
    assert "OLD" not in out
    assert "NEW" in out
    assert out.startswith("top")
    assert out.rstrip().endswith("bottom")

def test_read_json_default(tmp_path):
    assert fsutil.read_json(str(tmp_path / "none.json"), default={"x": 1}) == {"x": 1}
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m pytest tests/test_fsutil_marker.py -v`
Expected: FAIL — `ModuleNotFoundError: pw.fsutil`.

- [ ] **Step 3: 최소 구현**

Create `pw/fsutil.py`:

```python
import json, os, re

def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

def upsert_marker_block(text, block, begin, end):
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    new_block = f"{begin}\n{block}\n{end}"
    if pattern.search(text):
        return pattern.sub(new_block, text)
    sep = "" if text.endswith("\n") or text == "" else "\n"
    return f"{text}{sep}\n{new_block}\n"
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m pytest tests/test_fsutil_marker.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw/fsutil.py tests/test_fsutil_marker.py
git commit -m "feat: json rw + marker block upsert"
```

---

### Task 4: settings.json 병합 (allowlist/denylist, 보존)

**Files:**
- Modify: `pw/fsutil.py`
- Test: `tests/test_fsutil_settings.py`

**Interfaces:**
- Produces: `pw.fsutil.merge_enabled_plugins(existing: dict, enable: list[str], disable: list[str]) -> dict` — `existing`의 다른 키를 보존하고 `enabledPlugins`만 갱신: `enable`은 `True`, `disable`은 `False`. `enable`이 `disable`보다 우선. 기존 `enabledPlugins`의 다른 키는 유지.

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_fsutil_settings.py`:

```python
from pw import fsutil

def test_merge_preserves_other_keys_and_sets_flags():
    existing = {"permissions": {"allow": ["x"]},
                "enabledPlugins": {"keep@m": True, "context7@cpo": True}}
    out = fsutil.merge_enabled_plugins(
        existing,
        enable=["a@m", "b@m"],
        disable=["context7@cpo", "c@m"])
    assert out["permissions"] == {"allow": ["x"]}          # 보존
    assert out["enabledPlugins"]["a@m"] is True
    assert out["enabledPlugins"]["b@m"] is True
    assert out["enabledPlugins"]["context7@cpo"] is False   # denylist가 덮어씀
    assert out["enabledPlugins"]["c@m"] is False
    assert out["enabledPlugins"]["keep@m"] is True          # 기존 유지

def test_enable_wins_over_disable():
    out = fsutil.merge_enabled_plugins({}, enable=["a@m"], disable=["a@m"])
    assert out["enabledPlugins"]["a@m"] is True
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m pytest tests/test_fsutil_settings.py -v`
Expected: FAIL — `AttributeError: merge_enabled_plugins`.

- [ ] **Step 3: 최소 구현** — `pw/fsutil.py`에 추가:

```python
import copy

def merge_enabled_plugins(existing, enable, disable):
    out = copy.deepcopy(existing) if existing else {}
    ep = dict(out.get("enabledPlugins", {}))
    for s in disable:
        ep[s] = False
    for s in enable:      # enable 이 disable 을 이김
        ep[s] = True
    out["enabledPlugins"] = ep
    return out
```

(파일 상단 import에 `copy` 추가.)

- [ ] **Step 4: 통과 확인**

Run: `python3 -m pytest tests/test_fsutil_settings.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw/fsutil.py tests/test_fsutil_settings.py
git commit -m "feat: merge_enabled_plugins allowlist/denylist"
```

---

### Task 5: 언어/능력 감지

**Files:**
- Create: `pw/detect.py`
- Test: `tests/test_detect.py`

**Interfaces:**
- Consumes: `capabilityTags` (presets.json)
- Produces:
  - `pw.detect.detect_capabilities(project_dir: str, capability_tags: dict) -> set[str]` — 감지된 언어/능력 태그 집합. 마커 형식: `"파일명"`=존재, `"파일명::substr"`=존재+내용포함, `"*.확장자"`=glob 매칭. `existing-code`는 project_dir에 `*.py/*.ts/*.js/*.go/*.rs` 소스가 하나라도 있으면(단 `.claude/`, `docs/`, `node_modules/` 제외) 포함.
  - `pw.detect.lsp_slugs(capabilities: set[str], lsp_for: dict) -> list[str]` — 감지 언어의 LSP 슬러그 목록(입력 dict 순서).

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_detect.py`:

```python
from pw import detect

TAGS = {"typescript": ["package.json", "tsconfig.json"],
        "python": ["pyproject.toml"],
        "frontend": ["package.json::react"],
        "infra": ["*.tf"]}
LSP_FOR = {"typescript": "typescript-lsp@cpo", "python": "pyright-lsp@cpo"}

def test_detects_file_and_content_and_glob(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies":{"react":"^18"}}')
    (tmp_path / "main.tf").write_text("resource {}")
    (tmp_path / "app.py").write_text("x=1")
    caps = detect.detect_capabilities(str(tmp_path), TAGS)
    assert "typescript" in caps      # package.json 존재
    assert "frontend" in caps        # react 포함
    assert "infra" in caps           # *.tf
    assert "existing-code" in caps    # app.py
    assert "python" not in caps       # pyproject.toml 없음

def test_lsp_slugs_maps_detected_languages():
    caps = {"typescript", "frontend"}
    assert detect.lsp_slugs(caps, LSP_FOR) == ["typescript-lsp@cpo"]
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m pytest tests/test_detect.py -v`
Expected: FAIL — `ModuleNotFoundError: pw.detect`.

- [ ] **Step 3: 최소 구현**

Create `pw/detect.py`:

```python
import os, glob

SOURCE_EXTS = (".py", ".ts", ".js", ".go", ".rs")
IGNORE_DIRS = {".claude", "docs", "node_modules", ".git"}

def _marker_hit(project_dir, marker):
    if "::" in marker:
        fname, substr = marker.split("::", 1)
        p = os.path.join(project_dir, fname)
        return os.path.exists(p) and substr in open(p, encoding="utf-8", errors="ignore").read()
    if "*" in marker:
        return bool(glob.glob(os.path.join(project_dir, marker)))
    return os.path.exists(os.path.join(project_dir, marker))

def _has_source(project_dir):
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        if any(f.endswith(SOURCE_EXTS) for f in files):
            return True
    return False

def detect_capabilities(project_dir, capability_tags):
    caps = set()
    for cap, markers in capability_tags.get("detect", {}).items():
        if any(_marker_hit(project_dir, m) for m in markers):
            caps.add(cap)
    if _has_source(project_dir):
        caps.add("existing-code")
    return caps

def lsp_slugs(capabilities, lsp_for):
    return [slug for lang, slug in lsp_for.items() if lang in capabilities]
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m pytest tests/test_detect.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw/detect.py tests/test_detect.py
git commit -m "feat: language/capability detection"
```

---

### Task 6: 유효 플러그인 집합 계산

**Files:**
- Modify: `pw/data.py`
- Test: `tests/test_data_effective.py`

**Interfaces:**
- Produces:
  - `pw.data.plugin_name(slug: str) -> str` — `@` 앞부분 반환 (`context7@cpo` → `context7`).
  - `pw.data.effective_plugins(presets: dict, preset_name: str, always_on: list[str], lsp_slugs: list[str]) -> list[str]` — 프리셋 plugins + alwaysOn + (lspByLanguage 프리셋이면 lsp_slugs) 를 합쳐 **중복 제거·순서 보존**. 존재하지 않는 preset_name은 `KeyError`.

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_data_effective.py`:

```python
import pytest
from pw import data

PRESETS = {"web": {"plugins": ["a@m", "b@m"]},
           "min": {"plugins": ["a@m"], "lspByLanguage": True}}
ALWAYS = ["sp@dev", "am@am"]

def test_plugin_name():
    assert data.plugin_name("context7@claude-plugins-official") == "context7"

def test_effective_dedup_and_order():
    eff = data.effective_plugins(PRESETS, "web", ALWAYS, lsp_slugs=["ts@cpo"])
    assert eff == ["a@m", "b@m", "sp@dev", "am@am"]   # web 은 lspByLanguage 아님 → lsp 제외

def test_effective_includes_lsp_when_flagged():
    eff = data.effective_plugins(PRESETS, "min", ALWAYS, lsp_slugs=["ts@cpo", "py@cpo"])
    assert eff == ["a@m", "sp@dev", "am@am", "ts@cpo", "py@cpo"]

def test_unknown_preset_raises():
    with pytest.raises(KeyError):
        data.effective_plugins(PRESETS, "ghost", ALWAYS, lsp_slugs=[])
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m pytest tests/test_data_effective.py -v`
Expected: FAIL — `AttributeError: plugin_name`.

- [ ] **Step 3: 최소 구현** — `pw/data.py`에 추가:

```python
def plugin_name(slug):
    return slug.split("@", 1)[0]

def effective_plugins(presets, preset_name, always_on, lsp_slugs):
    if preset_name not in presets:
        raise KeyError(preset_name)
    preset = presets[preset_name]
    ordered = list(preset.get("plugins", [])) + list(always_on)
    if preset.get("lspByLanguage"):
        ordered += list(lsp_slugs)
    seen, result = set(), []
    for s in ordered:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m pytest tests/test_data_effective.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw/data.py tests/test_data_effective.py
git commit -m "feat: effective_plugins + plugin_name"
```

---

### Task 7: 플레이북 생성

**Files:**
- Create: `pw/playbook.py`
- Test: `tests/test_playbook.py`

**Interfaces:**
- Consumes: `pw.data.plugin_name`
- Produces: `pw.playbook.generate_playbook(preset_name, phase_model, effective_slugs, capabilities, lsp_slugs, invocation_rules) -> str` — 마커(`<!-- pw:begin schemaVersion=1 preset=... -->` … `<!-- pw:end -->`)로 감싼 마크다운.
  - **도구 포함 규칙** (역할별): tool이 `superpowers:`/`/code-review`/`gh`/`agentmemory:` 로 시작 → 항상 포함(alwaysOn/builtin). `__lsp_by_language__` → `lsp_slugs`의 plugin_name들로 확장(비면 그 줄 생략). 그 외 → `plugin_name(tool)`이 effective_slugs의 plugin_name 집합에 있을 때만. 추가로 role에 `whenCapability`가 있으면 그 capability가 `capabilities`에 있을 때만.
  - 각 단계 헤더 + 포함된 역할을 번호로 나열. 마지막에 "호출 규칙" 섹션(invocation_rules 요약).

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_playbook.py`:

```python
from pw import playbook

PHASE_MODEL = {
    "phases": ["brainstorm", "implement", "review"],
    "roles": {
        "brainstorm": [
            {"role": "설계", "tool": "superpowers:brainstorming"},
            {"role": "기존코드", "tool": "understand-anything", "whenCapability": "existing-code"},
        ],
        "implement": [
            {"role": "LSP", "tool": "__lsp_by_language__"},
            {"role": "테스트", "tool": "test-writer-fixer"},
            {"role": "UI", "tool": "frontend-design", "whenCapability": "frontend"},
        ],
        "review": [{"role": "주력", "tool": "/code-review"}],
    },
}
RULES = {"orchestrator": {"primary": "superpowers", "rescueOnly": ["codex"]},
         "memory": {"single": "agentmemory"}}

def test_playbook_includes_available_excludes_missing():
    md = playbook.generate_playbook(
        preset_name="backend-api",
        phase_model=PHASE_MODEL,
        effective_slugs=["test-writer-fixer@awesome-claude-plugins", "superpowers@superpowers-dev"],
        capabilities=set(),                 # existing-code, frontend 없음
        lsp_slugs=["pyright-lsp@claude-plugins-official"],
        invocation_rules=RULES)
    assert md.startswith("<!-- pw:begin")
    assert md.rstrip().endswith("<!-- pw:end -->")
    assert "superpowers:brainstorming" in md          # builtin
    assert "understand-anything" not in md            # capability 없음
    assert "pyright-lsp" in md                        # LSP 확장
    assert "test-writer-fixer" in md                  # effective 에 있음
    assert "frontend-design" not in md                # frontend capability 없음
    assert "/code-review" in md
    assert "superpowers" in md and "codex" in md      # 호출 규칙 섹션

def test_playbook_omits_lsp_line_when_no_lsp():
    md = playbook.generate_playbook("minimal", PHASE_MODEL,
        effective_slugs=[], capabilities=set(), lsp_slugs=[], invocation_rules=RULES)
    assert "__lsp_by_language__" not in md
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m pytest tests/test_playbook.py -v`
Expected: FAIL — `ModuleNotFoundError: pw.playbook`.

- [ ] **Step 3: 최소 구현**

Create `pw/playbook.py`:

```python
from pw.data import plugin_name

BEGIN_TMPL = "<!-- pw:begin schemaVersion=1 preset={preset} -->"
END = "<!-- pw:end -->"
_ALWAYS_PREFIXES = ("superpowers:", "/code-review", "gh", "agentmemory:")

def _resolve(role, effective_names, capabilities, lsp_slugs):
    """이 역할이 플레이북에 포함되면 표시 문자열, 아니면 None."""
    if role.get("whenCapability") and role["whenCapability"] not in capabilities:
        return None
    tool = role["tool"]
    if tool == "__lsp_by_language__":
        names = [plugin_name(s) for s in lsp_slugs]
        return ", ".join(names) if names else None
    if tool.startswith(_ALWAYS_PREFIXES):
        return tool
    return tool if plugin_name(tool) in effective_names else None

def generate_playbook(preset_name, phase_model, effective_slugs, capabilities, lsp_slugs, invocation_rules):
    effective_names = {plugin_name(s) for s in effective_slugs}
    lines = [BEGIN_TMPL.format(preset=preset_name),
             f"# 프로젝트 플레이북 — {preset_name}",
             "> 현재 단계는 .claude/project-state.json. /phase-next 로 진행.", ""]
    for phase in phase_model["phases"]:
        lines.append(f"## {phase}")
        n = 1
        for role in phase_model["roles"].get(phase, []):
            shown = _resolve(role, effective_names, capabilities, lsp_slugs)
            if shown is not None:
                lines.append(f"{n}. {role['role']} — {shown}")
                n += 1
        if n == 1:
            lines.append("_(이 단계에 활성 도구 없음)_")
        lines.append("")
    orch = invocation_rules.get("orchestrator", {})
    mem = invocation_rules.get("memory", {})
    lines += ["## 호출 규칙 (충돌 가드)",
              f"- 오케스트레이터: {orch.get('primary')} 하나. {', '.join(orch.get('rescueOnly', []))} 는 rescue 시에만.",
              f"- 메모리: {mem.get('single')} 하나.",
              "- 리뷰: /code-review 주력 먼저 → 전문 리뷰어는 트리거 시 → 새 지적 없으면 정지.",
              END]
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m pytest tests/test_playbook.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw/playbook.py tests/test_playbook.py
git commit -m "feat: playbook generation with availability rules"
```

---

### Task 8: 상태 파일 + 단계 전환

**Files:**
- Create: `pw/state.py`
- Test: `tests/test_state.py`

**Interfaces:**
- Consumes: `pw.fsutil.read_json`, `pw.fsutil.write_json`
- Produces:
  - `pw.state.default_state(preset, phases, detected_langs) -> dict` — `{schemaVersion:1, preset, phase:phases[0], phases, detectedLanguages, history:[]}`.
  - `pw.state.advance(state) -> dict` — 다음 단계로 이동한 새 dict. 마지막 단계면 그대로 두고 `state["_atEnd"]=True`. history에 `{phase, at}` append (`at`은 인자로 받은 `now` 문자열).
  - 시그니처: `advance(state, now: str) -> dict`.

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_state.py`:

```python
from pw import state

PHASES = ["brainstorm", "plan", "implement"]

def test_default_state():
    s = state.default_state("web", PHASES, ["python"])
    assert s["schemaVersion"] == 1
    assert s["preset"] == "web"
    assert s["phase"] == "brainstorm"
    assert s["phases"] == PHASES
    assert s["detectedLanguages"] == ["python"]
    assert s["history"] == []

def test_advance_moves_to_next_and_records_history():
    s = state.default_state("web", PHASES, [])
    s2 = state.advance(s, now="2026-07-06T00:00:00Z")
    assert s2["phase"] == "plan"
    assert s2["history"][-1] == {"phase": "plan", "at": "2026-07-06T00:00:00Z"}
    assert "_atEnd" not in s2

def test_advance_at_last_phase_flags_end():
    s = state.default_state("web", PHASES, [])
    s["phase"] = "implement"
    s2 = state.advance(s, now="t")
    assert s2["phase"] == "implement"
    assert s2["_atEnd"] is True
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m pytest tests/test_state.py -v`
Expected: FAIL — `ModuleNotFoundError: pw.state`.

- [ ] **Step 3: 최소 구현**

Create `pw/state.py`:

```python
import copy

def default_state(preset, phases, detected_langs):
    return {"schemaVersion": 1, "preset": preset, "phase": phases[0],
            "phases": list(phases), "detectedLanguages": list(detected_langs), "history": []}

def advance(state, now):
    s = copy.deepcopy(state)
    phases = s["phases"]
    i = phases.index(s["phase"])
    if i >= len(phases) - 1:
        s["_atEnd"] = True
        return s
    s["phase"] = phases[i + 1]
    s.setdefault("history", []).append({"phase": s["phase"], "at": now})
    return s
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m pytest tests/test_state.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw/state.py tests/test_state.py
git commit -m "feat: project state + phase advance"
```

---

### Task 9: CLI — init 서브명령

**Files:**
- Create: `pw/cli.py`
- Test: `tests/test_cli_init.py`

**Interfaces:**
- Consumes: `pw.data`, `pw.detect`, `pw.fsutil`, `pw.playbook`, `pw.state`
- Produces: `pw.cli.cmd_init(project_dir, preset, presets_path, installed_path, now, dry_run=False, force=False) -> dict` — 결과 요약 dict `{written: [...], enabled: [...], disabled: [...], missing: [...], dryRun: bool}`. `dry_run`이면 파일 안 씀. 이미 `project-state.json` 있고 `force=False`면 `RuntimeError("already initialized; use --repair or --force")`.
  - denylist = (installed 집합) − (effective 집합).
  - `.claude/settings.json`, `.claude/playbook.md`, `.claude/project-state.json`, `CLAUDE.md` 포인터를 씀.

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_cli_init.py`:

```python
import json, os
from pw import cli

def _installed(tmp_path):
    slugs = ["context7@claude-plugins-official", "superpowers@superpowers-dev",
             "agentmemory@agentmemory", "andrej-karpathy-skills@karpathy-skills",
             "static-analysis@trailofbits", "kesekit@kesekit",
             "security-guidance@claude-plugins-official", "code-simplifier@claude-plugins-official",
             "understand-anything@understand-anything"]
    p = tmp_path / "installed.json"
    p.write_text(json.dumps({"plugins": {s: [{}] for s in slugs}}))
    return str(p)

PRESETS = os.path.join(os.path.dirname(__file__), "..", "pw", "presets.json")

def test_init_writes_files_and_denylists_non_preset(tmp_path):
    proj = tmp_path / "proj"; proj.mkdir()
    res = cli.cmd_init(str(proj), "security-audit", PRESETS, _installed(tmp_path),
                       now="2026-07-06T00:00:00Z")
    settings = json.loads((proj / ".claude" / "settings.json").read_text())
    ep = settings["enabledPlugins"]
    assert ep["static-analysis@trailofbits"] is True          # 프리셋
    assert ep["superpowers@superpowers-dev"] is True           # alwaysOn
    assert ep["context7@claude-plugins-official"] is False     # 非프리셋 → denylist
    assert (proj / ".claude" / "playbook.md").exists()
    state = json.loads((proj / ".claude" / "project-state.json").read_text())
    assert state["preset"] == "security-audit" and state["phase"] == "brainstorm"
    assert "playbook" in (proj / "CLAUDE.md").read_text()

def test_init_dry_run_writes_nothing(tmp_path):
    proj = tmp_path / "proj2"; proj.mkdir()
    res = cli.cmd_init(str(proj), "minimal", PRESETS, _installed(tmp_path),
                       now="t", dry_run=True)
    assert res["dryRun"] is True
    assert not (proj / ".claude").exists()

def test_init_refuses_reinit_without_force(tmp_path):
    proj = tmp_path / "proj3"; proj.mkdir()
    cli.cmd_init(str(proj), "minimal", PRESETS, _installed(tmp_path), now="t")
    try:
        cli.cmd_init(str(proj), "minimal", PRESETS, _installed(tmp_path), now="t")
        assert False, "should have raised"
    except RuntimeError as e:
        assert "already initialized" in str(e)
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m pytest tests/test_cli_init.py -v`
Expected: FAIL — `ModuleNotFoundError: pw.cli`.

- [ ] **Step 3: 최소 구현**

Create `pw/cli.py`:

```python
import os
from pw import data, detect, fsutil, playbook, state

CLAUDE_PTR = ("이 프로젝트는 .claude/playbook.md 의 단계별 워크플로우를 따른다. "
              "현재 단계는 .claude/project-state.json 참조.")
PTR_BEGIN, PTR_END = "<!-- pw:begin -->", "<!-- pw:end -->"

def _paths(project_dir):
    c = os.path.join(project_dir, ".claude")
    return {"claude": c,
            "settings": os.path.join(c, "settings.json"),
            "playbook": os.path.join(c, "playbook.md"),
            "state": os.path.join(c, "project-state.json"),
            "claudemd": os.path.join(project_dir, "CLAUDE.md")}

def cmd_init(project_dir, preset, presets_path, installed_path, now, dry_run=False, force=False):
    p = _paths(project_dir)
    if os.path.exists(p["state"]) and not force and not dry_run:
        raise RuntimeError("already initialized; use --repair or --force")
    presets = data.load_presets(presets_path)
    installed = data.installed_plugins(installed_path)
    caps = detect.detect_capabilities(project_dir, presets["capabilityTags"])
    caps |= set(presets["presets"].get(preset, {}).get("capabilities", []))
    lsp = detect.lsp_slugs(caps, presets["capabilityTags"]["lspFor"])
    effective = data.effective_plugins(presets["presets"], preset, presets["alwaysOn"], lsp)
    enable, missing = data.validate_slugs(effective, installed)
    disable = [s for s in sorted(installed) if s not in set(enable)]
    pb = playbook.generate_playbook(preset, presets["phaseModel"], enable, caps, lsp,
                                    presets["invocationRules"])
    st = state.default_state(preset, presets["phaseModel"]["phases"], sorted(caps))
    result = {"enabled": enable, "disabled": disable, "missing": missing,
              "dryRun": dry_run, "written": []}
    if dry_run:
        return result
    settings = fsutil.merge_enabled_plugins(fsutil.read_json(p["settings"], {}), enable, disable)
    fsutil.write_json(p["settings"], settings)
    os.makedirs(p["claude"], exist_ok=True)
    with open(p["playbook"], "w", encoding="utf-8") as f:
        f.write(pb)
    fsutil.write_json(p["state"], st)
    existing_md = ""
    if os.path.exists(p["claudemd"]):
        existing_md = open(p["claudemd"], encoding="utf-8").read()
    with open(p["claudemd"], "w", encoding="utf-8") as f:
        f.write(fsutil.upsert_marker_block(existing_md, CLAUDE_PTR, PTR_BEGIN, PTR_END))
    result["written"] = [p["settings"], p["playbook"], p["state"], p["claudemd"]]
    return result
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m pytest tests/test_cli_init.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw/cli.py tests/test_cli_init.py
git commit -m "feat: cmd_init with denylist + dry-run + reinit guard"
```

---

### Task 10: CLI — phase-next / status / activate + argparse main

**Files:**
- Modify: `pw/cli.py`
- Test: `tests/test_cli_more.py`

**Interfaces:**
- Consumes: `pw.state`, `pw.fsutil`
- Produces:
  - `pw.cli.cmd_phase_next(project_dir, now) -> dict` — 상태 읽어 advance, 저장, `{phase, atEnd, guidance}` 반환. guidance는 playbook.md의 해당 단계 섹션 텍스트.
  - `pw.cli.cmd_status(project_dir) -> dict` — `{preset, phase, enabled, disabled}` 반환. 파일 없으면 `RuntimeError("not initialized")`.
  - `pw.cli.main(argv) -> int` — `argparse`로 `init|phase-next|status|activate` 디스패치.

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_cli_more.py`:

```python
import json, os
from pw import cli

PRESETS = os.path.join(os.path.dirname(__file__), "..", "pw", "presets.json")

def _installed(tmp_path):
    slugs = ["context7@claude-plugins-official", "superpowers@superpowers-dev",
             "agentmemory@agentmemory", "andrej-karpathy-skills@karpathy-skills"]
    p = tmp_path / "installed.json"
    p.write_text(json.dumps({"plugins": {s: [{}] for s in slugs}}))
    return str(p)

def test_phase_next_advances_and_returns_guidance(tmp_path):
    proj = tmp_path / "p"; proj.mkdir()
    cli.cmd_init(str(proj), "minimal", PRESETS, _installed(tmp_path), now="t")
    out = cli.cmd_phase_next(str(proj), now="2026-07-06T01:00:00Z")
    assert out["phase"] == "plan"
    assert out["atEnd"] is False
    assert "plan" in out["guidance"]
    st = json.loads((proj / ".claude" / "project-state.json").read_text())
    assert st["phase"] == "plan"

def test_status_returns_current(tmp_path):
    proj = tmp_path / "p2"; proj.mkdir()
    cli.cmd_init(str(proj), "minimal", PRESETS, _installed(tmp_path), now="t")
    s = cli.cmd_status(str(proj))
    assert s["preset"] == "minimal"
    assert s["phase"] == "brainstorm"

def test_status_uninitialized_raises(tmp_path):
    proj = tmp_path / "empty"; proj.mkdir()
    try:
        cli.cmd_status(str(proj)); assert False
    except RuntimeError as e:
        assert "not initialized" in str(e)
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m pytest tests/test_cli_more.py -v`
Expected: FAIL — `AttributeError: cmd_phase_next`.

- [ ] **Step 3: 최소 구현** — `pw/cli.py`에 추가:

```python
import argparse, re

def _phase_section(playbook_text, phase):
    m = re.search(rf"(^## {re.escape(phase)}\b.*?)(?=^## |\Z)", playbook_text, re.DOTALL | re.MULTILINE)
    return m.group(1).strip() if m else ""

def cmd_phase_next(project_dir, now):
    p = _paths(project_dir)
    st = fsutil.read_json(p["state"])
    if st is None:
        raise RuntimeError("not initialized")
    st2 = state.advance(st, now)
    fsutil.write_json(p["state"], st2)
    pb = open(p["playbook"], encoding="utf-8").read() if os.path.exists(p["playbook"]) else ""
    return {"phase": st2["phase"], "atEnd": st2.get("_atEnd", False),
            "guidance": _phase_section(pb, st2["phase"])}

def cmd_status(project_dir):
    p = _paths(project_dir)
    st = fsutil.read_json(p["state"])
    if st is None:
        raise RuntimeError("not initialized")
    settings = fsutil.read_json(p["settings"], {})
    ep = settings.get("enabledPlugins", {})
    return {"preset": st["preset"], "phase": st["phase"],
            "enabled": [k for k, v in ep.items() if v],
            "disabled": [k for k, v in ep.items() if not v]}

def cmd_activate(project_dir, slug, installed_path):
    p = _paths(project_dir)
    installed = data.installed_plugins(installed_path)
    if slug not in installed:
        raise RuntimeError(f"not installed: {slug}")
    settings = fsutil.merge_enabled_plugins(fsutil.read_json(p["settings"], {}), [slug], [])
    fsutil.write_json(p["settings"], settings)
    return {"activated": slug, "note": "restart session to load"}

def main(argv):
    import datetime
    ap = argparse.ArgumentParser(prog="pw")
    sub = ap.add_subparsers(dest="cmd", required=True)
    home = os.path.expanduser("~")
    dflt_presets = os.path.join(home, ".claude", "project-presets.json")
    dflt_installed = os.path.join(home, ".claude", "plugins", "installed_plugins.json")
    pi = sub.add_parser("init"); pi.add_argument("preset"); pi.add_argument("--dry-run", action="store_true")
    pi.add_argument("--force", action="store_true")
    sub.add_parser("phase-next"); sub.add_parser("status")
    pa = sub.add_parser("activate"); pa.add_argument("slug")
    args = ap.parse_args(argv)
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    cwd = os.getcwd()
    if args.cmd == "init":
        out = cmd_init(cwd, args.preset, dflt_presets, dflt_installed, now,
                       dry_run=args.dry_run, force=args.force)
    elif args.cmd == "phase-next":
        out = cmd_phase_next(cwd, now)
    elif args.cmd == "status":
        out = cmd_status(cwd)
    elif args.cmd == "activate":
        out = cmd_activate(cwd, args.slug, dflt_installed)
    import json as _json
    print(_json.dumps(out, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m pytest tests/test_cli_more.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw/cli.py tests/test_cli_more.py
git commit -m "feat: phase-next/status/activate + argparse main"
```

---

### Task 11: 슬래시 명령 md + install.sh + 통합 테스트

**Files:**
- Create: `commands/project-init.md`, `commands/phase-next.md`, `commands/project-status.md`, `commands/project-activate.md`
- Create: `install.sh`
- Test: `tests/test_integration.py`

**Interfaces:**
- Consumes: `pw.cli.main`
- Produces: 설치 스크립트 + 슬래시 명령. `install.sh`는 `pw/`, `commands/*.md`, `pw/presets.json`을 `~/.claude/`로 복사.

- [ ] **Step 1: 통합 실패 테스트 작성**

Create `tests/test_integration.py`:

```python
import json, os
from pw import cli

PRESETS = os.path.join(os.path.dirname(__file__), "..", "pw", "presets.json")

def test_end_to_end_init_then_phase_next(tmp_path, monkeypatch):
    proj = tmp_path / "app"; proj.mkdir()
    (proj / "pyproject.toml").write_text("[project]\nname='x'")
    (proj / "svc.py").write_text("x=1")
    inst = tmp_path / "installed.json"
    slugs = ["context7@claude-plugins-official", "superpowers@superpowers-dev",
             "agentmemory@agentmemory", "andrej-karpathy-skills@karpathy-skills",
             "pyright-lsp@claude-plugins-official"]
    inst.write_text(json.dumps({"plugins": {s: [{}] for s in slugs}}))
    res = cli.cmd_init(str(proj), "minimal", PRESETS, str(inst), now="t")
    # 언어 감지로 pyright LSP 가 활성에 포함
    assert "pyright-lsp@claude-plugins-official" in res["enabled"]
    pb = (proj / ".claude" / "playbook.md").read_text()
    assert "pyright-lsp" in pb
    out = cli.cmd_phase_next(str(proj), now="t2")
    assert out["phase"] == "plan"
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m pytest tests/test_integration.py -v`
Expected: PASS 또는 FAIL — 이 테스트는 기존 코드로 통과해야 정상(회귀 확인용). 만약 LSP 확장이 minimal 프리셋(`lspByLanguage:true`)에서 안 되면 FAIL → 원인 수정.

- [ ] **Step 3: 슬래시 명령 + install.sh 작성**

Create `commands/project-init.md`:

```markdown
---
description: 새 프로젝트에 프리셋을 적용하고 단계별 플레이북을 생성한다
argument-hint: [preset] [--dry-run|--force]
---
현재 폴더에서 프로젝트 프리셋 워크플로우를 초기화한다.

사용자가 프리셋을 인자로 주지 않았으면, 먼저 `python3 ~/.claude/pw/cli.py status` 를 시도해 이미 초기화됐는지 보고, 아니면 폴더의 package.json/pyproject.toml 등을 근거로 프리셋(web-fullstack/backend-api/security-audit/docs-deck/minimal) 중 하나를 추천하고 확인받는다.

확정되면 실행: `python3 ~/.claude/pw/cli.py init <preset>` (미리보기는 `--dry-run`).
출력 요약을 사용자에게 보여주고, **"새 세션에서 플러그인이 로드된다"** 는 점과 다음 스텝(`/phase-next`)을 안내한다.
$ARGUMENTS
```

Create `commands/phase-next.md`:

```markdown
---
description: 워크플로우를 다음 단계로 진행하고 그 단계의 도구 가이드를 출력한다
---
`python3 ~/.claude/pw/cli.py phase-next` 를 실행하고, 반환된 guidance(현재 단계 도구 순서)를 사용자에게 보여준다. atEnd 가 true 면 마지막 단계임을 알린다.
```

Create `commands/project-status.md`:

```markdown
---
description: 현재 프리셋·단계·활성 플러그인을 보여준다
---
`python3 ~/.claude/pw/cli.py status` 를 실행하고 결과(preset, phase, enabled/disabled)를 표로 정리해 보여준다.
```

Create `commands/project-activate.md`:

```markdown
---
description: 프리셋 밖 플러그인을 이 프로젝트에 추가 활성화한다
argument-hint: <plugin@marketplace>
---
`python3 ~/.claude/pw/cli.py activate $ARGUMENTS` 를 실행하고, "재시작 시 로드됨" 안내를 전달한다.
```

Create `install.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
DEST="$HOME/.claude"
mkdir -p "$DEST/commands" "$DEST/pw"
cp -R pw/. "$DEST/pw/"
cp pw/presets.json "$DEST/project-presets.json"
cp commands/*.md "$DEST/commands/"
echo "설치 완료: $DEST/pw, $DEST/commands, $DEST/project-presets.json"
echo "명령: /project-init  /phase-next  /project-status  /project-activate"
```

참고: `cli.py`의 argparse 기본 경로는 `~/.claude/project-presets.json` 과 `~/.claude/plugins/installed_plugins.json` 를 가리키므로, 설치 후 실 사용 시 프리셋 원천은 `~/.claude/project-presets.json`이다.

- [ ] **Step 4: 전체 테스트 통과 확인**

Run: `python3 -m pytest -v`
Expected: PASS (모든 테스트 그린)

- [ ] **Step 5: 커밋**

```bash
git add commands/ install.sh tests/test_integration.py
git commit -m "feat: slash commands + install.sh + e2e integration test"
```

---

## Self-Review 결과

- **Spec coverage:** 프리셋/단계모델(T1,7) · 슬러그검증(T2) · settings 병합+denylist(T4,9) · 마커 보존(T3) · 언어감지(T5) · 유효집합(T6) · 플레이북(T7) · 상태/전환(T8) · init/phase-next/status/activate(T9,10) · 명령·설치(T11) · CLAUDE.md 포인터(T9) · 멱등/dry-run/force(T9) · MCP는 문서화만(비목표) — 전 항목 태스크 매핑됨.
- **Placeholder scan:** 모든 코드 스텝에 실제 코드/테스트 포함, TODO 없음.
- **Type consistency:** `effective_plugins`/`plugin_name`(T6) → playbook(T7)·cli(T9)에서 동일 시그니처 사용. `advance(state, now)`(T8) → cli(T10)에서 동일. `merge_enabled_plugins(existing, enable, disable)`(T4) → cli(T9,10)에서 동일. 일관.

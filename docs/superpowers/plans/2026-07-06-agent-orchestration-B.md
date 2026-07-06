# B — 특화 서브에이전트 오케스트레이션 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 구체 작업에 대해 이미 로드된 플러그인 에이전트·스킬 중 최적을 골라 디스패치 "계획"을 만드는 `/route` 명령 + 얇은 종합 전문가 2종(security-auditor·test-engineer)을 만든다.

**Architecture:** 결정적 부분(에이전트 live 조회·규칙 매칭·라우팅 컨텍스트 생성)은 순수 파이썬 패키지 `pw_route/`가, 판단·디스패치는 메인 Claude가 실행하는 얇은 슬래시 명령/에이전트 마크다운이 담당한다. A의 `install.sh`를 확장해 함께 배포한다.

**Tech Stack:** Python 3.10+ 표준 라이브러리만, pytest, 마크다운 에이전트/명령, JSON 규칙.

## Global Constraints

- Python 3.10+ 표준 라이브러리만 — 외부 의존성 금지.
- 테스트는 `./venv/bin/python -m pytest` 로 실행(시스템 python3엔 pytest 없음).
- `pw_route/cli.py`는 스크립트로 실행(`python3 ~/.claude/pw_route/cli.py …`)되므로 **맨 위에 sys.path 부트스트랩** 필수(A에서 겪은 교차 임포트 버그 방지).
- `/route`는 자율 실행자가 아니라 **디스패치 계획 생성기**. 명령 마크다운은 그 점을 명시.
- B는 스킬·원본 플러그인 에이전트 파일을 **절대 수정하지 않는다**(INV-1). 직접 매치되는 원본 에이전트를 우선(INV-2). 종합은 이견 보존(INV-3).
- 전문가·명령 마크다운은 **구조화 출력 계약** 키를 포함: `findings, evidence, inspected, confidence, unresolved, next`.
- 스키마 버전 = 1.
- 기존 `~/.claude/agents/*.md`(pptx 등)를 덮어쓰지 않는다 — 신규 이름만 사용(security-auditor·test-engineer).

---

### Task 1: pw_route 패키지 + route-rules.json + 규칙 로드

**Files:**
- Create: `pw_route/__init__.py` (빈 파일)
- Create: `pw_route/rules.py`
- Create: `pw_route/route-rules.json`
- Test: `tests/test_route_rules_load.py`

**Interfaces:**
- Produces: `pw_route.rules.load_rules(path: str) -> dict` — route-rules.json 로드, `schemaVersion==1` 검증, `rules`(list)·`fallback`(str) 키 필수. 위반 시 `ValueError`.

- [ ] **Step 1: route-rules.json 작성**

Create `pw_route/route-rules.json`:

```json
{
  "schemaVersion": 1,
  "rules": [
    {
      "domain": "security",
      "match": ["보안", "security", "취약", "vuln", "audit", "감사"],
      "prefer": "security-auditor",
      "narrow": [{ "when": ["semgrep"], "use": "semgrep-scanner" }, { "when": ["codeql"], "use": "semgrep-scanner" }]
    },
    {
      "domain": "test",
      "match": ["테스트", "test", "커버리지", "coverage", "단위", "unit"],
      "prefer": "test-engineer",
      "narrow": []
    }
  ],
  "fallback": "prefer-original-plugin-agents"
}
```

- [ ] **Step 2: 실패 테스트 작성**

Create `tests/test_route_rules_load.py`:

```python
import json, os, pytest
from pw_route import rules

RULES = os.path.join(os.path.dirname(__file__), "..", "pw_route", "route-rules.json")

def test_load_rules_ok():
    d = rules.load_rules(RULES)
    assert d["schemaVersion"] == 1
    assert isinstance(d["rules"], list) and len(d["rules"]) >= 2
    assert d["fallback"] == "prefer-original-plugin-agents"
    assert any(r["domain"] == "security" for r in d["rules"])

def test_load_rules_bad_schema(tmp_path):
    p = tmp_path / "bad.json"; p.write_text(json.dumps({"schemaVersion": 2}))
    with pytest.raises(ValueError):
        rules.load_rules(str(p))
```

- [ ] **Step 3: 실패 확인**

Run: `./venv/bin/python -m pytest tests/test_route_rules_load.py -v`
Expected: FAIL — `ModuleNotFoundError: pw_route`.

- [ ] **Step 4: 최소 구현**

Create `pw_route/__init__.py` (빈 파일). Create `pw_route/rules.py`:

```python
import json

def load_rules(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("schemaVersion") != 1:
        raise ValueError(f"unsupported schemaVersion: {d.get('schemaVersion')}")
    for k in ("rules", "fallback"):
        if k not in d:
            raise ValueError(f"missing key: {k}")
    if not isinstance(d["rules"], list):
        raise ValueError("rules must be a list")
    return d
```

- [ ] **Step 5: 통과 확인**

Run: `./venv/bin/python -m pytest tests/test_route_rules_load.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: 커밋**

```bash
git add pw_route/__init__.py pw_route/rules.py pw_route/route-rules.json tests/test_route_rules_load.py
git commit -m "feat(B): route-rules.json + load_rules"
```

---

### Task 2: 에이전트 live 조회 (frontmatter 파싱)

**Files:**
- Create: `pw_route/discover.py`
- Test: `tests/test_route_discover.py`

**Interfaces:**
- Produces:
  - `pw_route.discover.parse_frontmatter(text: str) -> dict` — `---`로 감싼 상단 블록에서 `name`/`description`/`tools` 단순 스칼라 추출(폴디드 `>-` 값은 빈 문자열). frontmatter 없으면 `{}`.
  - `pw_route.discover.discover_agents(dirs: list[str]) -> list[dict]` — 각 dir의 `*.md`를 읽어 `{"name","description","tools","path","source"}` 리스트(name 있는 것만). `source`는 그 dir 경로. 중복 name은 첫 등장 우선.

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_route_discover.py`:

```python
from pw_route import discover

FM = """---
name: security-auditor
description: >-
  Audits security across tools.
tools: Bash, Read, Glob
---
body here
"""

def test_parse_frontmatter():
    d = discover.parse_frontmatter(FM)
    assert d["name"] == "security-auditor"
    assert d["tools"] == "Bash, Read, Glob"

def test_parse_frontmatter_none():
    assert discover.parse_frontmatter("no frontmatter here") == {}

def test_discover_agents_reads_dir(tmp_path):
    (tmp_path / "a.md").write_text("---\nname: alpha\ntools: Read\n---\nx")
    (tmp_path / "b.md").write_text("---\nname: beta\n---\ny")
    (tmp_path / "note.txt").write_text("ignored")
    agents = discover.discover_agents([str(tmp_path)])
    names = sorted(a["name"] for a in agents)
    assert names == ["alpha", "beta"]
    assert all("path" in a and "source" in a for a in agents)

def test_discover_dedup_first_wins(tmp_path):
    d1 = tmp_path / "d1"; d1.mkdir(); (d1 / "a.md").write_text("---\nname: dup\n---\n1")
    d2 = tmp_path / "d2"; d2.mkdir(); (d2 / "a.md").write_text("---\nname: dup\n---\n2")
    agents = discover.discover_agents([str(d1), str(d2)])
    assert len([a for a in agents if a["name"] == "dup"]) == 1
    assert agents[0]["source"] == str(d1)
```

- [ ] **Step 2: 실패 확인**

Run: `./venv/bin/python -m pytest tests/test_route_discover.py -v`
Expected: FAIL — `ModuleNotFoundError: pw_route.discover`.

- [ ] **Step 3: 최소 구현**

Create `pw_route/discover.py`:

```python
import os, glob

def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    out = {}
    for line in block.splitlines():
        if ":" not in line or line[:1] in (" ", "\t"):
            continue  # skip indented continuation / folded lines
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith((">", "|")):
            val = ""  # folded/literal scalar: value is on following indented lines
        if key in ("name", "description", "tools"):
            out[key] = val
    return out

def discover_agents(dirs):
    seen, result = set(), []
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "*.md"))):
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            fm = parse_frontmatter(text)
            name = fm.get("name")
            if not name or name in seen:
                continue
            seen.add(name)
            result.append({"name": name, "description": fm.get("description", ""),
                           "tools": fm.get("tools", ""), "path": path, "source": d})
    return result
```

- [ ] **Step 4: 통과 확인**

Run: `./venv/bin/python -m pytest tests/test_route_discover.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw_route/discover.py tests/test_route_discover.py
git commit -m "feat(B): live agent discovery via frontmatter"
```

---

### Task 3: 규칙 매칭

**Files:**
- Modify: `pw_route/rules.py`
- Test: `tests/test_route_match.py`

**Interfaces:**
- Consumes: `pw_route.rules.load_rules`
- Produces: `pw_route.rules.match_task(task: str, rules_doc: dict, available_names: set[str]) -> dict` — 반환:
  `{"domain": str|None, "prefer": {"name": str, "available": bool}|None, "narrow": {"name": str, "available": bool}|None, "fallback": str, "matched": bool}`.
  로직: `task` 소문자화; `rules` 순회하며 어떤 `match` 키워드가 task에 부분포함되면 그 규칙 선택(첫 매치). `prefer`의 available은 `name in available_names`. `narrow` 리스트에서 `when` 키워드가 모두 task에 포함되는 첫 항목의 `use`를 narrow로(available 판정 포함). 매치 없으면 domain/prefer/narrow=None, matched=False, fallback은 항상 rules_doc["fallback"].

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_route_match.py`:

```python
import os
from pw_route import rules

RULES = os.path.join(os.path.dirname(__file__), "..", "pw_route", "route-rules.json")

def test_match_security_prefer_available():
    doc = rules.load_rules(RULES)
    r = rules.match_task("이 코드 보안 점검해줘", doc, {"security-auditor"})
    assert r["matched"] is True
    assert r["domain"] == "security"
    assert r["prefer"] == {"name": "security-auditor", "available": True}
    assert r["narrow"] is None

def test_match_narrow_semgrep_unavailable():
    doc = rules.load_rules(RULES)
    r = rules.match_task("run a semgrep security scan", doc, {"security-auditor"})
    assert r["narrow"] == {"name": "semgrep-scanner", "available": False}

def test_no_match_returns_fallback():
    doc = rules.load_rules(RULES)
    r = rules.match_task("write me a poem", doc, set())
    assert r["matched"] is False
    assert r["prefer"] is None
    assert r["fallback"] == "prefer-original-plugin-agents"
```

- [ ] **Step 2: 실패 확인**

Run: `./venv/bin/python -m pytest tests/test_route_match.py -v`
Expected: FAIL — `AttributeError: match_task`.

- [ ] **Step 3: 최소 구현** — `pw_route/rules.py`에 추가:

```python
def _avail(name, available_names):
    return {"name": name, "available": name in available_names}

def match_task(task, rules_doc, available_names):
    t = (task or "").lower()
    result = {"domain": None, "prefer": None, "narrow": None,
              "fallback": rules_doc.get("fallback"), "matched": False}
    for rule in rules_doc.get("rules", []):
        if any(kw.lower() in t for kw in rule.get("match", [])):
            result["matched"] = True
            result["domain"] = rule.get("domain")
            if rule.get("prefer"):
                result["prefer"] = _avail(rule["prefer"], available_names)
            for n in rule.get("narrow", []):
                if all(kw.lower() in t for kw in n.get("when", [])):
                    result["narrow"] = _avail(n["use"], available_names)
                    break
            break
    return result
```

- [ ] **Step 4: 통과 확인**

Run: `./venv/bin/python -m pytest tests/test_route_match.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw_route/rules.py tests/test_route_match.py
git commit -m "feat(B): rule matching with availability"
```

---

### Task 4: CLI — 라우팅 컨텍스트 + sys.path 부트스트랩 + main

**Files:**
- Create: `pw_route/cli.py`
- Test: `tests/test_route_cli.py`

**Interfaces:**
- Consumes: `pw_route.discover`, `pw_route.rules`
- Produces:
  - `pw_route.cli.default_agent_dirs(home: str, cwd: str) -> list[str]` — `[cwd/.claude/agents, home/.claude/agents] + glob(home/.claude/plugins/cache/*/*/*/agents)` 중 **존재하는** 디렉토리만.
  - `pw_route.cli.route(task, rules_path, agent_dirs) -> dict` — discover→match 후 라우팅 컨텍스트 반환: `{"task", "domain", "prefer", "narrow", "fallback", "matched", "availableAgents": [names], "note"}`. prefer/narrow가 unavailable이면 `note`에 "capability unavailable in this session; enable preset and restart" 포함.
  - `pw_route.cli.main(argv) -> int` — argparse `route <task>` 서브명령, 결과 JSON 출력. 기본 rules_path=`~/.claude/route-rules.json`.
  - 파일 맨 위 **sys.path 부트스트랩** 포함.

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_route_cli.py`:

```python
import os, sys, subprocess, json
from pw_route import cli

RULES = os.path.join(os.path.dirname(__file__), "..", "pw_route", "route-rules.json")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_route_security_available(tmp_path):
    agents = tmp_path / "agents"; agents.mkdir()
    (agents / "security-auditor.md").write_text("---\nname: security-auditor\n---\nx")
    ctx = cli.route("보안 점검해줘", RULES, [str(agents)])
    assert ctx["domain"] == "security"
    assert ctx["prefer"] == {"name": "security-auditor", "available": True}
    assert "security-auditor" in ctx["availableAgents"]

def test_route_unavailable_adds_restart_note(tmp_path):
    agents = tmp_path / "agents"; agents.mkdir()  # empty → security-auditor absent
    ctx = cli.route("보안 취약점 semgrep 스캔", RULES, [str(agents)])
    assert ctx["prefer"] == {"name": "security-auditor", "available": False}
    assert "restart" in ctx["note"].lower()

def test_default_agent_dirs_filters_existing(tmp_path):
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    dirs = cli.default_agent_dirs(str(tmp_path), str(tmp_path))
    assert any(d.endswith("/.claude/agents") for d in dirs)

def test_cli_runs_as_script_without_import_error(tmp_path):
    # 설치 경로처럼 스크립트로 직접 실행 → 임포트 크래시 없어야 함
    r = subprocess.run([sys.executable, os.path.join(REPO, "pw_route", "cli.py")],
                       capture_output=True, text=True, cwd=str(tmp_path))
    assert "ModuleNotFoundError" not in r.stderr
    assert r.returncode == 2   # argparse: missing subcommand
```

- [ ] **Step 2: 실패 확인**

Run: `./venv/bin/python -m pytest tests/test_route_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: pw_route.cli` 또는 (script test) ModuleNotFoundError.

- [ ] **Step 3: 최소 구현**

Create `pw_route/cli.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse, glob, json
from pw_route import discover, rules

RESTART_NOTE = "capability unavailable in this session; enable preset and restart (/project-activate)"

def default_agent_dirs(home, cwd):
    candidates = [os.path.join(cwd, ".claude", "agents"),
                  os.path.join(home, ".claude", "agents")]
    candidates += glob.glob(os.path.join(home, ".claude", "plugins", "cache", "*", "*", "*", "agents"))
    return [d for d in candidates if os.path.isdir(d)]

def route(task, rules_path, agent_dirs):
    agents = discover.discover_agents(agent_dirs)
    names = {a["name"] for a in agents}
    doc = rules.load_rules(rules_path)
    m = rules.match_task(task, doc, names)
    note = ""
    for slot in ("prefer", "narrow"):
        if m[slot] and not m[slot]["available"]:
            note = RESTART_NOTE
    return {"task": task, "domain": m["domain"], "prefer": m["prefer"],
            "narrow": m["narrow"], "fallback": m["fallback"], "matched": m["matched"],
            "availableAgents": sorted(names), "note": note}

def main(argv):
    ap = argparse.ArgumentParser(prog="pw_route")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("route"); pr.add_argument("task")
    pr.add_argument("--rules", default=os.path.join(os.path.expanduser("~"), ".claude", "route-rules.json"))
    args = ap.parse_args(argv)
    home, cwd = os.path.expanduser("~"), os.getcwd()
    if args.cmd == "route":
        out = route(args.task, args.rules, default_agent_dirs(home, cwd))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: 통과 확인**

Run: `./venv/bin/python -m pytest tests/test_route_cli.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 커밋**

```bash
git add pw_route/cli.py tests/test_route_cli.py
git commit -m "feat(B): routing-context CLI + sys.path bootstrap"
```

---

### Task 5: 전문가 에이전트 정의 (불변식 포함)

**Files:**
- Create: `agents/security-auditor.md`
- Create: `agents/test-engineer.md`
- Test: `tests/test_route_agents_md.py`

**Interfaces:**
- Produces: 두 에이전트 마크다운. 테스트는 필수 문구 포함을 검증(INV-1 미수정 원칙 · 구조화 출력 키 · 폴백 언급).

- [ ] **Step 1: 실패 테스트 작성**

Create `tests/test_route_agents_md.py`:

```python
import os

AGENTS = os.path.join(os.path.dirname(__file__), "..", "agents")
STRUCT_KEYS = ["findings", "evidence", "inspected", "confidence", "unresolved", "next"]

def _read(name):
    return open(os.path.join(AGENTS, name), encoding="utf-8").read()

def test_security_auditor_has_frontmatter_and_invariants():
    t = _read("security-auditor.md")
    assert t.startswith("---")
    assert "name: security-auditor" in t
    assert "수정하지 않는다" in t          # INV-1 (원본 미수정)
    for k in STRUCT_KEYS:
        assert k in t                        # 구조화 출력 계약
    assert "폴백" in t or "fallback" in t.lower()

def test_test_engineer_has_frontmatter_and_invariants():
    t = _read("test-engineer.md")
    assert t.startswith("---")
    assert "name: test-engineer" in t
    assert "수정하지 않는다" in t
    for k in STRUCT_KEYS:
        assert k in t
```

- [ ] **Step 2: 실패 확인**

Run: `./venv/bin/python -m pytest tests/test_route_agents_md.py -v`
Expected: FAIL — `FileNotFoundError: agents/security-auditor.md`.

- [ ] **Step 3: 최소 구현**

Create `agents/security-auditor.md`:

```markdown
---
name: security-auditor
description: >-
  이미 설치된 보안 스킬(kesekit KISA 점검, static-analysis의 /semgrep·/codeql,
  security-guidance)을 한 격리 컨텍스트에서 돌려 결과를 중복제거·우선순위화하고
  이견을 보존해 종합한다. "보안 점검/취약점 감사/security review" 요청에 사용.
tools: Bash, Read, Glob, Grep
model: sonnet
---

너는 교차-플러그인 보안 종합가다. 아래 불변식을 지킨다.

## 불변식
- 어떤 스킬·플러그인 에이전트 파일도 **수정하지 않는다**. 읽고 실행만 한다.
- 원본 스킬의 결과를 재해석·재구현하지 않는다. 그대로 인용한다.
- 서로 다른 스킬의 이견을 합치지 말고 **보존**한다.

## 절차
1. 사용 가능한 것만 실행: kesekit 점검 스킬, `/semgrep`(가능하면 `/codeql`), security-guidance 가이드.
   - 스킬이 없으면 그 관점을 생략하고 리포트에 폴백으로 명시한다.
2. 각 도구 원출력을 수집한다(파일·라인·명령 근거 포함).
3. 중복 지적을 합치되 출처를 잃지 않는다.

## 출력 계약 (반드시 이 구조로 반환)
- findings: 발견 목록(각 항목에 출처 도구 표기)
- evidence: 파일/라인/명령 출력
- inspected: 조사한 파일·명령
- confidence: high | med | low
- unresolved: 미해결 질문·이견
- next: 권장 다음 행동

## 과장 금지
"도구가 X 보고"를 "X는 확실히 익스플로잇 가능"으로 승격하지 않는다 — 근거가 명확할 때만.
```

Create `agents/test-engineer.md`:

```markdown
---
name: test-engineer
description: >-
  test-writer-fixer 스킬과 감지 언어 LSP, 테스트 러너를 한 격리 컨텍스트에서
  돌려 테스트 작성→실행→실패분석→수정 루프를 수행하고 커버리지 갭을 종합한다.
  "테스트 작성/수정/커버리지" 요청에 사용.
tools: Bash, Read, Write, Edit, Glob
model: sonnet
---

너는 테스트 종합가다. 아래 불변식을 지킨다.

## 불변식
- 스킬·플러그인 에이전트 파일을 **수정하지 않는다**(대상 코드의 테스트만 작성/수정).
- test-writer-fixer 등 원본 스킬의 동작을 재구현하지 않고 호출한다.
- 통과/실패 결과를 임의로 낙관하지 않는다 — 실제 러너 출력을 근거로 삼는다.

## 절차
1. 대상 코드의 테스트를 작성/보강한다(test-writer-fixer 스킬 활용, 없으면 폴백 명시).
2. 실제 러너로 실행한다(pytest/jest 등, 감지 언어에 맞게).
3. 실패를 분석해 최소 수정하고 재실행한다. 커버리지 갭을 정리한다.

## 출력 계약 (반드시 이 구조로 반환)
- findings: 추가/수정한 테스트, 남은 갭
- evidence: 러너 명령과 실제 출력(통과/실패 수)
- inspected: 조사한 파일·명령
- confidence: high | med | low
- unresolved: 미해결 실패·불확실 영역
- next: 권장 다음 행동
```

- [ ] **Step 4: 통과 확인**

Run: `./venv/bin/python -m pytest tests/test_route_agents_md.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add agents/security-auditor.md agents/test-engineer.md tests/test_route_agents_md.py
git commit -m "feat(B): security-auditor + test-engineer specialist agents"
```

---

### Task 6: /route 명령 + install.sh 확장 + 통합 테스트

**Files:**
- Create: `commands/route.md`
- Modify: `install.sh`
- Test: `tests/test_route_integration.py`

**Interfaces:**
- Consumes: `pw_route.cli`
- Produces: `/route` 명령 마크다운 + 확장된 install.sh(pw_route·agents·route.md·route-rules.json 복사). 통합 테스트는 discover→match→route end-to-end + install.sh 안전성.

- [ ] **Step 1: 통합 실패 테스트 작성**

Create `tests/test_route_integration.py`:

```python
import os, subprocess
from pw_route import cli

RULES = os.path.join(os.path.dirname(__file__), "..", "pw_route", "route-rules.json")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_end_to_end_route_with_real_specialist_agents(tmp_path):
    # 실제 저장소의 agents/ 를 조회 대상으로 사용 → security-auditor 존재 → prefer available
    agents_dir = os.path.join(REPO, "agents")
    ctx = cli.route("이 저장소 보안 감사", RULES, [agents_dir])
    assert ctx["domain"] == "security"
    assert ctx["prefer"] == {"name": "security-auditor", "available": True}
    assert ctx["note"] == ""   # 사용 가능하므로 재시작 안내 없음

def test_install_sh_syntax_ok():
    r = subprocess.run(["bash", "-n", os.path.join(REPO, "install.sh")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
```

- [ ] **Step 2: 실패 확인**

Run: `./venv/bin/python -m pytest tests/test_route_integration.py -v`
Expected: FAIL — `test_end_to_end...`는 Task 5의 agents가 있으면 통과할 수 있으나, install.sh에 pw_route 복사가 없으므로 이 태스크의 목적은 명령·설치 추가. (두 테스트 모두 통과할 때까지 진행.)

- [ ] **Step 3: /route 명령 + install.sh 확장 작성**

Create `commands/route.md`:

```markdown
---
description: 작업에 맞는 특화 에이전트 디스패치 "계획"을 만든다 (실행은 메인이 함)
argument-hint: <작업 설명>
---
이 명령은 **자율 실행자가 아니라 디스패치 계획 생성기**다.

1. 라우팅 컨텍스트를 얻는다: `python3 ~/.claude/pw_route/cli.py route "$ARGUMENTS"`
   - 반환: domain, prefer(가용여부), narrow, fallback, availableAgents, note.
2. note 에 "restart" 안내가 있으면 → 사용자에게 "이 세션엔 해당 능력이 없음, 프리셋 켜고 재시작(/project-activate)"을 전하고 멈춘다.
3. 아니면 **디스패치 계획**을 만든다:
   - 광범위 보안 → security-auditor, 정밀 semgrep 전용 → 원본 semgrep-scanner, 테스트 → test-engineer, 미지 작업 → 원본 플러그인 에이전트 우선(fallback).
   - 각 선택의 이유 · 병렬 안전 여부 · 각 서브에이전트에 줄 정확한 프롬프트 · 기대 출력 계약(findings/evidence/inspected/confidence/unresolved/next) · 종합 체크리스트.
4. 계획대로 서브에이전트를 디스패치한다(병렬 가능). **원본 스킬·에이전트는 수정하지 않는다.**
5. 결과를 종합한다 — 이견을 보존하고, 각 주요 주장에 출처 에이전트를 표기하며, 과장하지 않는다.
```

Modify `install.sh` — 기존 마지막 `echo` 줄들 앞에 아래 복사 블록을 추가(기존 A 복사 블록은 유지):

```bash
# --- subsystem B: agent orchestration ---
mkdir -p "$DEST/pw_route" "$DEST/agents"
cp -R pw_route/. "$DEST/pw_route/"
cp pw_route/route-rules.json "$DEST/route-rules.json"
cp agents/security-auditor.md agents/test-engineer.md "$DEST/agents/"
cp commands/route.md "$DEST/commands/"
```

(파일 끝의 안내 `echo` 에 `/route` 를 덧붙인다.)

- [ ] **Step 4: 전체 통과 확인**

Run: `./venv/bin/python -m pytest -q`
Expected: PASS (모든 테스트 그린)

- [ ] **Step 5: 커밋**

```bash
git add commands/route.md install.sh tests/test_route_integration.py
git commit -m "feat(B): /route command + install.sh + integration test"
```

---

## Self-Review 결과

- **Spec coverage:** 전문가 2종(T5) · /route 계획 생성기(T4,T6) · route-rules + live 조회(T1,T2,T3,T4) · 저하0 불변식 INV-1/2/3(T5 문구·T3/T6 우선순위) · 구조화 출력(T5,T6) · 동적 플러그인 한계 재시작 안내(T4 note) · A/B 경계(B는 단계상태 없음 — 구조상 미포함) · 설치(T6) · 카탈로그 연기(persistent 없음, live 조회) — 전 항목 매핑됨.
- **Placeholder scan:** 모든 코드/마크다운 스텝에 실제 내용 포함, TODO 없음.
- **Type consistency:** `load_rules`(T1)→`match_task`(T3)→`route`(T4) 동일 사용. `discover_agents`(T2)→`route`(T4) 동일. `default_agent_dirs`/`route`(T4)→통합(T6) 동일. sys.path 부트스트랩(T4)은 A에서 검증된 패턴. 일관.

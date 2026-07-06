# ccpilot

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![tests](https://img.shields.io/badge/tests-48%20passing-brightgreen.svg)
![deps](https://img.shields.io/badge/dependencies-none%20(stdlib)-success.svg)
![for](https://img.shields.io/badge/for-Claude%20Code-8A2BE2.svg)

**프로젝트마다 Claude Code 플러그인·에이전트를 최적으로 구성해주는 워크플로우 툴킷.**

`ccpilot`은 두 개의 사용자 레벨 확장으로 이루어져 있다:

- **A — 프로젝트 프리셋 워크플로우:** 새 프로젝트에서 프리셋으로 플러그인을 활성화하고, 그 조합에 맞는 **단계별 플레이북**(brainstorm → plan → implement → review → ship)을 자동 생성한다.
- **B — 에이전트 오케스트레이션:** 구체 작업에 맞는 특화 에이전트로 라우팅하는 **디스패치 계획**을 만들고, 격리 컨텍스트에서 실행·종합한다. 원본 스킬·에이전트는 절대 수정하지 않는다.

순수 Python 표준 라이브러리 + 마크다운 슬래시 명령/에이전트로 구현했다. 외부 의존성 없음.

---

## 설치

**요구사항:** [Claude Code](https://code.claude.com) · Python 3.10+ · git. (런타임 외부 의존성은 없다 — 표준 라이브러리만 쓴다.)

```bash
git clone https://github.com/KimHands/ccpilot.git
cd ccpilot
bash install.sh
```

`install.sh`가 하는 일:

- `pw/`·`pw_route/` → `~/.claude/`
- `commands/*.md` → `~/.claude/commands/` (`/project-init` `/phase-next` `/project-status` `/project-activate` `/route`)
- `agents/security-auditor.md`·`test-engineer.md` → `~/.claude/agents/`
- `pw/presets.json` → `~/.claude/project-presets.json`, `pw_route/route-rules.json` → `~/.claude/route-rules.json`

**가산 설치** — 기존 사용자 에이전트·설정을 덮어쓰지 않는다. 설치 후 **Claude Code를 재시작**하면 명령이 로드된다.

<details>
<summary>제거</summary>

```bash
rm -rf ~/.claude/pw ~/.claude/pw_route
rm -f  ~/.claude/commands/{project-init,phase-next,project-status,project-activate,route}.md
rm -f  ~/.claude/agents/{security-auditor,test-engineer}.md
rm -f  ~/.claude/project-presets.json ~/.claude/route-rules.json
```
</details>

## 데모

```console
$ cd my-new-app        # (pyproject.toml + .py 파일 존재)
> /project-init
  감지된 언어: python · 추천 프리셋: backend-api
  ✓ .claude/settings.json  (활성 8 · 비활성 12)
  ✓ .claude/playbook.md · project-state.json · CLAUDE.md
  → 새 세션에서 로드됨. 다음: /phase-next

> /route 이 코드 보안 감사해줘
  domain: security → security-auditor (available)
  plan: kesekit + /semgrep + security-guidance 병렬 → 종합
        출력 계약: findings/evidence/inspected/confidence/unresolved/next
```
> 실제 스크린샷·GIF는 추후 추가 예정.

---

## 사용법

### A — 프리셋 & 단계 워크플로우

```
/project-init                 # 프로젝트 유형 감지 → 프리셋 추천 → 적용
/project-init web-fullstack   # 프리셋 직접 지정
/project-init minimal --dry-run   # 변경 없이 미리보기

/phase-next                   # 다음 단계로 진행 + 그 단계 도구 가이드
/project-status               # 현재 프리셋·단계·활성 플러그인
/project-activate <plugin@marketplace>   # 프리셋 밖 도구 추가
```

`/project-init`은 프로젝트 `.claude/settings.json`(활성 플러그인 allowlist+denylist), `playbook.md`, `project-state.json`, `CLAUDE.md` 포인터를 생성한다. 플러그인은 세션 시작 시 로드되므로 init 후 **한 번 재시작**한다.

**프리셋:** `web-fullstack` · `backend-api` · `security-audit` · `docs-deck` · `minimal`. 정의는 `pw/presets.json` 하나에 있다 — 자유롭게 편집·추가 가능.

### B — 에이전트 라우팅

```
/route 이 코드 보안 감사해줘        # → security-auditor로 라우팅 계획
/route 테스트 작성하고 커버리지 확인  # → test-engineer로 라우팅 계획
```

`/route`는 **자율 실행자가 아니라 계획 생성기**다. `route-rules.json` + 설치된 에이전트를 live 조회해 최적 전문가를 고르고, 정확한 프롬프트·병렬 여부·출력 계약·종합 체크리스트가 담긴 디스패치 계획을 만든다. 실행·종합은 메인 세션이 한다.

**전문가 에이전트:** `security-auditor`(kesekit·semgrep·security-guidance 종합) · `test-engineer`(test-writer-fixer·LSP·러너). 둘 다 원본 스킬을 그대로 호출하고 구조화 출력(findings/evidence/inspected/confidence/unresolved/next)을 반환한다.

---

## 설계 원칙

- **저하 0:** 스킬·플러그인 에이전트 파일을 수정하지 않는다. 직접 매치되는 원본 에이전트를 우선한다. 종합 시 이견을 보존한다.
- **충돌 회피:** 오케스트레이터 하나 · 메모리 하나 · 리뷰는 주력 먼저 → 전문가는 트리거 시.
- **세션 시작 로드 제약 반영:** 프리셋은 init 때 한 번에 활성화(재시작 1회), 단계는 사용 안내. B는 이미 로드된 능력 사이에서만 라우팅한다.

---

## 저장소 구조

```
pw/            # A: 프리셋·단계·플레이북 (data·detect·fsutil·playbook·state·cli)
pw_route/      # B: 에이전트 라우팅 (discover·rules·cli)
agents/        # B: security-auditor·test-engineer 정의
commands/      # 슬래시 명령 (project-*·route)
install.sh     # ~/.claude 로 설치
tests/         # pytest (48 tests)
docs/superpowers/  # 설계 spec + 구현 plan (A·B)
```

## 개발

```bash
python3 -m venv venv && ./venv/bin/pip install pytest
./venv/bin/python -m pytest -q      # 48 passed
```

Python 3.10+ 표준 라이브러리만 사용한다(런타임 의존성 없음). 슬래시 명령은 `python3 ~/.claude/pw*/cli.py`를 스크립트로 실행하므로 각 `cli.py`는 sys.path 부트스트랩을 포함한다.

## 라이선스

MIT

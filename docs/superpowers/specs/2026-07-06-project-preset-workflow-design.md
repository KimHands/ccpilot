# 프로젝트 프리셋 & 단계별 워크플로우 시스템 — 설계 문서

- 작성일: 2026-07-06
- 상태: 설계 확정 대기 (코덱스 리뷰 반영본)
- 범위: **A — 프로젝트 도구 프로파일 매니저** (B 특화 서브에이전트 라이브러리는 후속)

## 1. 목적

새 프로젝트를 시작할 때 **프리셋으로 활성 플러그인을 고르고**, 그 조합에 맞는 **단계별 워크플로우(플레이북)** 를 자동 생성한다. 플레이북은 설치된 도구들의 강점을 충돌 없이 단계별로 배치해, "지금 무엇을 어떤 도구로 할지"를 지휘한다.

전제 사용자 환경: 플러그인 20개 + 개인 스킬 2개(academic-pptx, pptx-from-layouts) + MCP 8개(전부 연결).

## 2. 비목표 (이번 범위에서 제외)

- **B. 특화 서브에이전트 라이브러리** (보안/테스트 전용 에이전트) — 별도 spec
- **claude.ai 전역 커넥터 MCP의 프로젝트별 on/off** — 전역이라 제어 불가, 문서화만
- **SessionStart 훅 기반 단계 자동주입** — v2로 연기 (v1은 CLAUDE.md 포인터)
- **플러그인/마켓 패키징 배포** — 잘 돌아가면 v2에서 `kimhands/project-orchestrator`로

## 3. 검증된 Claude Code 메커니즘 (전제)

- `~/.claude/settings.json`의 `enabledPlugins` = `{"plugin@marketplace": true|false}`. 프로젝트 `.claude/settings.json`이 프로젝트 스코프로 override.
- **플러그인은 세션 시작 시 로드** — 도중 토글은 재시작해야 반영.
- 설정 우선순위: user → project → project.local (local이 최종 우선일 수 있음, CLI `--setting-sources`도 영향).
- 프로젝트 `.mcp.json` + `enabledMcpjsonServers`는 프로젝트 스코프 MCP만 제어. claude.ai 커넥터는 전역.
- SessionStart 훅은 `hookSpecificOutput.additionalContext`로 텍스트 주입 가능(읽기 전용). 대화형 UI 불가.
- 슬래시 명령 = `~/.claude/commands/*.md`(user) 또는 `<proj>/.claude/commands/*.md`(project).

## 4. 아키텍처 & 파일 구조

```
~/.claude/                         # 이 머신 전역 (한 번 설치)
├── commands/
│   ├── project-init.md            # /project-init [preset] [--dry-run|--repair|--force]
│   ├── phase-next.md              # /phase-next [--activate]
│   ├── project-status.md          # /project-status
│   └── project-activate.md        # /project-activate <plugin>
├── project-presets.json           # 단일 원천: 프리셋 + 단계모델 + 규칙 + 능력태그
└── scripts/
    └── project_workflow.py        # 결정적 파일 쓰기/검증 헬퍼 (명령이 호출)

<project>/.claude/                 # /project-init 이 생성
├── settings.json                  # enabledPlugins (allowlist true + denylist false)
├── playbook.md                    # 생성된 단계별 워크플로우 (생성블록 마커 포함)
└── project-state.json             # { preset, phase, phases[], history[], schemaVersion }
<project>/CLAUDE.md                # 플레이북 포인터 한 블록 추가(마커)
```

**설계 원칙**: `project-presets.json` 하나가 단일 원천. 명령어는 얇게(읽고 검증하고 결정적으로 쓰기). 파일 쓰기·검증 로직은 `project_workflow.py`에 모아 **명령(모델 매개)과 실제 변경(결정적 스크립트)을 분리** — 코덱스 지적(슬래시 명령만으로 대화형 설정은 불안정) 반영.

## 5. 데이터 모델 — `project-presets.json`

```jsonc
{
  "schemaVersion": 1,
  "alwaysOn": ["superpowers@superpowers-dev", "agentmemory@agentmemory",
               "andrej-karpathy-skills@karpathy-skills"],
  "phaseModel": {
    "phases": ["brainstorm", "plan", "implement", "review", "ship"],
    "roles": {
      "brainstorm": [
        { "role": "요구사항 취조", "tool": "grill-me", "optional": true },
        { "role": "설계 확정", "tool": "superpowers:brainstorming" },
        { "role": "기존코드 이해", "tool": "understand-anything", "whenCapability": "existing-code" }
      ],
      "plan": [
        { "role": "계획 작성", "tool": "superpowers:writing-plans" },
        { "role": "영향 분석", "tool": "understand-anything", "whenCapability": "existing-code" },
        { "role": "라이브러리 문서", "tool": "context7" }
      ],
      "implement": [
        { "role": "구현 루프", "tool": "superpowers:test-driven-development" },
        { "role": "언어 인텔리전스", "tool": "__lsp_by_language__" },
        { "role": "테스트 작성/수정", "tool": "test-writer-fixer" },
        { "role": "라이브러리 문서", "tool": "context7" },
        { "role": "UI 생성", "tool": "frontend-design", "whenCapability": "frontend" },
        { "role": "문서 산출물", "tool": "document-skills", "whenCapability": "docs-output" }
      ],
      "review": [
        { "role": "주력 리뷰", "tool": "/code-review" },
        { "role": "단순화", "tool": "code-simplifier" },
        { "role": "실시간 보안", "tool": "security-guidance" },
        { "role": "정적 보안", "tool": "static-analysis" },
        { "role": "한국 규제", "tool": "kesekit", "whenCapability": "kr-compliance" }
      ],
      "ship": [
        { "role": "커밋/PR", "tool": "gh" },
        { "role": "릴리스 문서", "tool": "document-skills" },
        { "role": "학습 영속", "tool": "agentmemory:remember" }
      ]
    }
  },
  "capabilityTags": {
    "detect": {
      "typescript": ["package.json", "tsconfig.json"],
      "python": ["pyproject.toml", "requirements.txt"],
      "go": ["go.mod"], "rust": ["Cargo.toml"],
      "frontend": ["package.json:react", "package.json:next"],
      "infra": ["Dockerfile", "*.tf"],
      "existing-code": ["src/**", ">10 source files"]
    },
    "toolFor": { "typescript": "typescript-lsp@claude-plugins-official",
                 "python": "pyright-lsp@claude-plugins-official" }
  },
  "presets": {
    "web-fullstack": { "plugins": ["typescript-lsp@...","pyright-lsp@...","frontend-design@...",
      "figma@...","vercel@...","context7@...","test-writer-fixer@awesome-claude-plugins",
      "code-simplifier@...","security-guidance@...","understand-anything@understand-anything"] },
    "backend-api": { "plugins": ["context7@claude-plugins-official",
      "test-writer-fixer@awesome-claude-plugins","static-analysis@trailofbits",
      "security-guidance@claude-plugins-official","code-simplifier@claude-plugins-official",
      "understand-anything@understand-anything"], "lspByLanguage": true },
    "security-audit": { "plugins": ["static-analysis@trailofbits","kesekit@kesekit",
      "security-guidance@...","understand-anything@...","code-simplifier@..."] },
    "docs-deck": { "plugins": ["document-skills@anthropic-agent-skills","felo-slides@felo-ai",
      "context7@..."], "personalSkills": ["academic-pptx","pptx-from-layouts"] },
    "minimal": { "plugins": ["context7@..."], "lspByLanguage": true }
  },
  "invocationRules": {
    "orchestrator": { "primary": "superpowers", "rescueOnly": ["codex"] },
    "memory": { "single": "agentmemory" },
    "review": { "primary": "/code-review",
                "specialists": ["code-simplifier","security-guidance","static-analysis","kesekit"],
                "order": "primary first → specialists on explicit trigger",
                "stopWhen": "no new findings" },
    "lsp": "one per detected language",
    "docs": { "general": "document-skills", "specialized": ["academic-pptx","pptx-from-layouts","felo-slides"] }
  }
}
```

**설계 결정**: 프리셋은 **plugins 목록만** 정의. 단계 배치는 `phaseModel`, 언어별 LSP는 `capabilityTags`로 **런타임 유도** → 다언어 프로젝트 대응(코덱스 #8).

## 6. 단계 모델 (5단계)

| 단계 | 역할 → 도구 (프리셋에 있을 때만 플레이북에 표시) |
|---|---|
| brainstorm | grill-me(선택) → superpowers:brainstorming → understand-anything(기존코드 시) |
| plan | superpowers:writing-plans → understand-anything(영향분석) → context7 |
| implement | superpowers TDD/subagent → LSP(감지언어) → test-writer-fixer → context7 → frontend-design/pptx(해당 시) |
| review | /code-review(주력) → code-simplifier → security-guidance → static-analysis(/semgrep) → kesekit(한국규제) |
| ship | gh CLI → document-skills(릴리스 문서) → agentmemory:remember(학습 영속) |

상시(alwaysOn): agentmemory · andrej-karpathy · superpowers.

## 7. 활성화 모델 (핵심 — 코덱스 반영)

**프리셋 = allowlist + denylist**:
- `/project-init`이 프로젝트 `.claude/settings.json`에 **프리셋+alwaysOn 플러그인 = `true`**, **현재 켜져 있는 非프리셋 플러그인 = `false`** 를 기록 → 프로젝트가 실제로 lean해짐(코덱스 #6).
- init 후 **세션 1회 재시작**으로 반영.
- **단계(phase)는 플러그인을 토글하지 않고 "사용 안내"** 만 함(사용자 확정 사항). `enabled`인 도구 중 그 단계에 쓸 것을 플레이북이 지휘.
- **`/phase-next --activate`(선택)**: 그 단계 전용 무거운 도구를 뒤늦게 켜고 싶을 때만 `enabledPlugins` 수정 + "재시작 시 로드" 안내.

**슬러그 검증**: 프리셋의 `plugin@marketplace` 키를 `~/.claude/plugins/installed_plugins.json`과 대조. 불일치 시 경고하고 건너뜀(조용한 누락 방지, 코덱스 #5). **로컬 설정 override 경고**: "effective config may be overridden by project.local settings" 안내.

## 8. 명령어 동작

모든 명령은 `project_workflow.py`를 호출해 **결정적**으로 파일을 읽고/검증하고/쓴다. 명령 md는 인자 파싱과 사용자 대화만 담당.

### `/project-init [preset] [--dry-run|--repair|--force]`
1. 인자로 preset 받음. 없으면 `capabilityTags.detect`로 프로젝트 언어/유형 감지 → 추천 프리셋 제시 후 확인.
2. **멱등성 검사**: 이미 `project-state.json` 있으면 `--force` 없이는 덮어쓰지 않고 `--repair` 안내.
3. 프리셋+alwaysOn 슬러그를 설치 목록과 대조·검증.
4. `.claude/settings.json` 병합 기록(기존 보존, allowlist `true`/denylist `false`).
5. `playbook.md` 생성(단계모델 ∩ 프리셋 ∩ 감지언어, **생성블록 마커** `<!-- pw:begin -->…<!-- pw:end -->`).
6. `project-state.json` = `{preset, phase:"brainstorm", phases, history:[], schemaVersion}`.
7. `CLAUDE.md`에 포인터 블록(마커) append (기존 내용 보존).
8. 출력: 활성/비활성 요약 · **"새 세션에서 로드됨"** · 다음 스텝. `--dry-run`이면 변경 없이 계획만 출력.

### `/phase-next [--activate]`
1. `project-state.json` 읽어 현재 단계 → 다음 단계 계산.
2. **검증**: 다음 단계 도구가 실제 설치·활성인지 확인, 아니면 경고.
3. state 갱신(history append).
4. 그 단계의 도구 사용 가이드(플레이북에서) 출력.
5. `--activate` 시에만 그 단계 추가 플러그인을 `enabledPlugins`에 켜고 재시작 안내.

### `/project-status`
- 현재 preset·phase·활성/비활성 플러그인 목록 + 이번 단계 가이드 + 드리프트 경고(설치≠설정 시).

### `/project-activate <plugin>`
- 프리셋 밖 플러그인 추가: 슬러그 검증 → `enabledPlugins` true → "재시작 시 로드".

## 9. `playbook.md` 형식

```md
<!-- pw:begin schemaVersion=1 preset=web-fullstack -->
# 프로젝트 플레이북 — web-fullstack (langs: typescript, python)
> 현재 단계는 .claude/project-state.json. /phase-next 로 진행.

## ① brainstorm
1. grill-me 로 요구사항 취조 (선택)
2. superpowers:brainstorming 로 설계 확정
- 상시: agentmemory 캡처 · superpowers 단일 오케스트레이터

## ② plan …
## ③ implement …  (LSP: typescript-lsp, pyright-lsp)
## ④ review …
## ⑤ ship …

## 호출 규칙 (충돌 가드)
- 오케스트레이터: superpowers 하나. codex는 /codex:rescue 시에만.
- 메모리: agentmemory 하나.
- 리뷰: /code-review 주력 먼저 → 전문 리뷰어는 트리거 시 → 새 지적 없으면 정지.
<!-- pw:end -->
```

## 10. `project-state.json` + 드리프트 방어

```json
{ "schemaVersion": 1, "preset": "web-fullstack",
  "phase": "brainstorm", "phases": ["brainstorm","plan","implement","review","ship"],
  "detectedLanguages": ["typescript","python"],
  "history": [{ "phase": "brainstorm", "at": "2026-07-06T10:00:00Z" }] }
```
- 모든 명령은 실행 전 **설치 목록 대조**로 드리프트(플러그인 삭제 등) 감지 → 경고.
- `--repair`: state·playbook·settings를 현재 설치 상태에 맞춰 재생성(생성블록만 교체, 사용자 편집 보존).

## 11. 소비 방식 (v1)

- **CLAUDE.md 포인터만** (SessionStart 훅 없음, 코덱스 #2). 마커 블록:
  ```
  <!-- pw:begin --> 이 프로젝트는 .claude/playbook.md 의 단계별 워크플로우를 따른다.
  현재 단계는 .claude/project-state.json 참조. <!-- pw:end -->
  ```
- Claude가 단계를 반복적으로 놓치는 게 관측되면 v2에서 SessionStart 훅(작은 텍스트 주입, append-only·멱등) 추가.

## 12. 언어/능력 감지

- init·status 시 `capabilityTags.detect`로 repo 파일 스캔 → `detectedLanguages`/capabilities 산출.
- 플레이북의 LSP·frontend·infra 항목은 감지 결과로 채움 → 다언어/혼합 프로젝트 정확.

## 13. 충돌 규칙 = 호출 규칙 (코덱스 #10)

"설치 하나"가 아니라 **호출 순서·정지 조건**으로 정의:
- 리뷰: 주력(/code-review) 먼저 → 전문(simplifier/security/static-analysis/kesekit)은 명시 트리거 → 새 지적 없으면 정지.
- 오케스트레이터/메모리는 여전히 단일(진짜 충돌).

## 14. MCP 처리 (코덱스 #7)

- `project_mcp`: `.mcp.json` 프로젝트 서버만 자동 관리(있을 때).
- `global_mcp_assumptions`: claude.ai 커넥터(Figma/Google/Notion/Gmail)·플러그인 MCP(context7/agentmemory/vercel)는 **"사용 가능하나 프리셋 관리 대상 아님"** 으로 플레이북에 사용 안내만.

## 15. 엣지 케이스 / 에러 처리

- **재-init**: `--force` 없이는 비파괴. `--repair`로 생성블록만 갱신.
- **삭제된 플러그인 참조**: 명령이 설치 목록 대조로 감지·경고·건너뜀.
- **로컬 설정 override**: init이 "project.local이 최종 우선일 수 있음" 경고.
- **사용자 수동 편집**: 생성블록 마커 밖 내용은 절대 건드리지 않음.
- **hooks 병합**: 훅 쓸 일 생기면 append-only·네임스페이스·멱등(v2).

## 16. 테스트 전략

- `project_workflow.py` 단위 테스트: 슬러그 검증, settings 병합(기존 보존/allowlist/denylist), 생성블록 마커 교체, 멱등(--dry-run 무변경), 언어 감지.
- 통합: 빈 폴더 → `/project-init web-fullstack --dry-run` → 계획 검증 → 실제 실행 → 파일 3종 + CLAUDE.md 확인 → `/phase-next` → state 전이 확인.
- 회귀: 기존 CLAUDE.md/settings.json 있는 프로젝트에서 사용자 내용 보존 확인.

## 17. 향후 (v2+)

- SessionStart 훅 단계 자동주입(필요 입증 시).
- **B. 특화 서브에이전트 라이브러리**(보안/테스트 전용 에이전트, 도구 스코핑 + 컨텍스트 격리).
- 플러그인/마켓 패키징으로 팀·다머신 공유.
- 프리셋 추가(mobile-rn, data-py 등).

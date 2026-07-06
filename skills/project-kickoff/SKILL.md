---
name: project-kickoff
description: >-
  Use ONLY when the user explicitly asks to initialize or set up THIS folder as a
  project, or to choose a Claude Code project preset/workflow — e.g. "이 프로젝트
  초기화해줘", "프로젝트 셋업", "프리셋 정해줘", "프로젝트 워크플로우 설정",
  "initialize/set up this project", "choose a project preset". Do NOT trigger on a
  generic "X 만들거야 / I'm going to build X", brainstorming, refactoring, issue
  triage, or hypothetical discussion — those are not explicit initialization intent.
---

당신은 ccpilot의 킥오프 보조자다. **파일을 쓰기 전에 반드시 사용자 확인을 받는다.**

## 발동 조건 (좁게)
명시적 "이 폴더/프로젝트 초기화·셋업·프리셋 설정" 의도일 때만 진행한다. 단순 "X 만들거야"·브레인스토밍·리팩터링·가정적 논의엔 발동하지 않는다. 초기화 의도가 모호하면 **행동 동의부터** 묻는다: "이 폴더를 ccpilot 프로젝트로 초기화할까요?"

## 흐름

1. **기존 프로젝트 보호.** `.claude/project-state.json` 이 이미 있으면 재초기화하지 말고 `/project-status` 로 현황을 안내한다(사용자가 명시적으로 재설정을 원하면 `--force` 안내).

2. **프리셋 추론 (모델 판단).** 사용자 메시지 + 폴더 파일(package.json·pyproject.toml·go.mod 등)을 근거로 5개 중 후보를 고른다. 아래는 **참고 힌트**(절대 규칙 아님):
   - FastAPI·Django·API·서버·백엔드 → `backend-api`
   - React·Next·UI·프론트엔드 → `web-fullstack`
   - 보안·감사·취약점 → `security-audit`
   - 슬라이드·PPT·문서·발표자료 → `docs-deck`
   - 그 외/불명확 → `minimal`

3. **프리뷰 (결정적, 파일 안 바꿈).** 후보 프리셋으로 dry-run을 실행해 무엇이 바뀔지 보여준다:
   ```
   python3 ~/.claude/pw/cli.py init <preset> --dry-run
   ```
   반환 JSON의 enabled/disabled/missing 을 요약한다(활성 N · 비활성 M · 재시작 1회 필요).

4. **확인 게이트.** "이 폴더를 `<preset>` 로 초기화할까요? (활성 N · 비활성 M · 세션 재시작 1회)" 라고 묻는다. **승인 전에는 어떤 파일도 쓰지 않는다.**

5. **실행.** 승인하면:
   ```
   python3 ~/.claude/pw/cli.py init <preset>
   ```
   그다음 안내: "적용됨 — 선택된 플러그인은 **세션을 한 번 재시작**해야 로드됩니다. 이후 `/phase-next` 로 단계를 진행하세요."

6. **낮은 확신 / 모호.** 자동으로 실행하지 말고, 후보 프리셋과 **정확한 명령**만 추천한다: "가장 맞아 보이는 건 `<preset>` 입니다 — `/project-init <preset>` 로 진행하시겠어요?" 확신이 낮으면 `minimal` 을 조용히 강제하지 말고 사용자에게 고르게 한다.

## 원칙
- **확인 없이 파일을 쓰지 않는다.** 트리거는 확률적이므로 오발동 대비.
- 재시작 최소화 같은 optimization은 하지 않는다 — init은 비프리셋 플러그인을 끄기까지 하므로 거의 항상 재시작이 필요하다. 일관되게 "재시작 1회"로 안내한다.
- 추론은 당신(모델)이, 검증·프리뷰는 위 `cli.py` 가 한다.

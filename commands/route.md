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

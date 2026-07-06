---
description: 새 프로젝트에 프리셋을 적용하고 단계별 플레이북을 생성한다
argument-hint: [preset] [--dry-run|--force]
---
현재 폴더에서 프로젝트 프리셋 워크플로우를 초기화한다.

사용자가 프리셋을 인자로 주지 않았으면, 먼저 `python3 ~/.claude/pw/cli.py status` 를 시도해 이미 초기화됐는지 보고, 아니면 폴더의 package.json/pyproject.toml 등을 근거로 프리셋(web-fullstack/backend-api/security-audit/docs-deck/minimal) 중 하나를 추천하고 확인받는다.

확정되면 실행: `python3 ~/.claude/pw/cli.py init <preset>` (미리보기는 `--dry-run`).
출력 요약을 사용자에게 보여주고, **"새 세션에서 플러그인이 로드된다"** 는 점과 다음 스텝(`/phase-next`)을 안내한다.
$ARGUMENTS

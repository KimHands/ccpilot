#!/usr/bin/env bash
set -euo pipefail
DEST="$HOME/.claude"
mkdir -p "$DEST/commands" "$DEST/pw"
cp -R pw/. "$DEST/pw/"
cp pw/presets.json "$DEST/project-presets.json"
cp commands/*.md "$DEST/commands/"

# --- subsystem B: agent orchestration ---
mkdir -p "$DEST/pw_route" "$DEST/agents"
cp -R pw_route/. "$DEST/pw_route/"
cp pw_route/route-rules.json "$DEST/route-rules.json"
cp agents/security-auditor.md agents/test-engineer.md "$DEST/agents/"
cp commands/route.md "$DEST/commands/"

# --- v2: SessionStart hook (멱등, 기존 훅 보존) ---
python3 pw/install_hook.py

# --- v3: intent-based kickoff skill ---
mkdir -p "$DEST/skills/project-kickoff"
cp skills/project-kickoff/SKILL.md "$DEST/skills/project-kickoff/"

echo "설치 완료: $DEST/pw, $DEST/commands, $DEST/project-presets.json"
echo "명령: /project-init  /phase-next  /project-status  /project-activate  /route"
echo "SessionStart 훅: 초기화된 프로젝트면 현재 단계를, 미설정이면 /project-init 을 자동 안내"
echo "킥오프 스킬: '이 프로젝트 초기화해줘' 발화 시 프리셋 추론→프리뷰→확인→init"

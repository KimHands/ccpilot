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

echo "설치 완료: $DEST/pw, $DEST/commands, $DEST/project-presets.json"
echo "명령: /project-init  /phase-next  /project-status  /project-activate  /route"

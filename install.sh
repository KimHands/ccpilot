#!/usr/bin/env bash
set -euo pipefail
DEST="$HOME/.claude"
mkdir -p "$DEST/commands" "$DEST/pw"
cp -R pw/. "$DEST/pw/"
cp pw/presets.json "$DEST/project-presets.json"
cp commands/*.md "$DEST/commands/"
echo "설치 완료: $DEST/pw, $DEST/commands, $DEST/project-presets.json"
echo "명령: /project-init  /phase-next  /project-status  /project-activate"

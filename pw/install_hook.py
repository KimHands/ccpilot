import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pw import fsutil

HOOK_CMD = "python3 ~/.claude/pw/hook_sessionstart.py"
MARKER = "hook_sessionstart.py"


def ensure_hook(settings_path):
    """~/.claude/settings.json 의 SessionStart 훅에 ccpilot 항목을 멱등 추가.
    기존 훅(Stop/Notification 등)은 보존. 이미 있으면 'present', 추가하면 'added'."""
    settings = fsutil.read_json(settings_path, {}) or {}
    hooks = settings.setdefault("hooks", {})
    ss = hooks.setdefault("SessionStart", [])
    for group in ss:
        for h in group.get("hooks", []):
            if MARKER in h.get("command", ""):
                return "present"
    ss.append({"hooks": [{"type": "command", "command": HOOK_CMD}]})
    fsutil.write_json(settings_path, settings)
    return "added"


def main():
    path = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
    print(f"SessionStart hook: {ensure_hook(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

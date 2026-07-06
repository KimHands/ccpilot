import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json, re
from pw import fsutil, detect


def _phase_section(playbook_text, phase):
    m = re.search(rf"(^## {re.escape(phase)}\b.*?)(?=^## |\Z)", playbook_text,
                  re.DOTALL | re.MULTILINE)
    return m.group(1).strip() if m else ""


def build_context(cwd):
    """세션 시작 시 주입할 컨텍스트 문자열. 주입할 게 없으면 ''."""
    claude = os.path.join(cwd, ".claude")
    state = fsutil.read_json(os.path.join(claude, "project-state.json"))
    if state:
        preset = state.get("preset", "?")
        phase = state.get("phase", "?")
        tools = ""
        pb = os.path.join(claude, "playbook.md")
        if os.path.exists(pb):
            with open(pb, encoding="utf-8", errors="ignore") as f:
                sec = _phase_section(f.read(), phase)
            tools = " · ".join(re.findall(r"—\s*(.+)", sec))
        line = f"ccpilot: preset={preset} · 현재 단계={phase}"
        if tools:
            line += f" · 이 단계 도구: {tools}"
        line += " · 다음: /phase-next · 플레이북: .claude/playbook.md"
        return line
    if detect._has_source(cwd):
        return "이 폴더는 ccpilot 미설정입니다 — /project-init 으로 프리셋·플레이북을 설정하세요."
    return ""


def main():
    try:
        ctx = build_context(os.getcwd())
    except Exception:
        ctx = ""  # fail-safe: 세션 시작을 절대 깨뜨리지 않는다
    if ctx:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": ctx}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

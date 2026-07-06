import os, sys, json, subprocess
from pw import hook_sessionstart as hook

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _init(tmp_path, phase="implement"):
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "project-state.json").write_text(json.dumps(
        {"schemaVersion": 1, "preset": "backend-api", "phase": phase,
         "phases": ["brainstorm", "plan", "implement"], "history": []}))
    (claude / "playbook.md").write_text(
        "<!-- pw:begin -->\n## plan\n1. 계획 — superpowers:writing-plans\n\n"
        "## implement\n1. 구현 루프 — superpowers:test-driven-development\n"
        "2. 언어 — pyright-lsp\n<!-- pw:end -->\n")
    return str(tmp_path)


def test_context_initialized_has_preset_phase_tools(tmp_path):
    ctx = hook.build_context(_init(tmp_path))
    assert "preset=backend-api" in ctx
    assert "implement" in ctx
    assert "test-driven-development" in ctx and "pyright-lsp" in ctx
    assert "/phase-next" in ctx


def test_context_suggests_when_uninitialized_with_source(tmp_path):
    (tmp_path / "main.py").write_text("x = 1")
    ctx = hook.build_context(str(tmp_path))
    assert "미설정" in ctx and "/project-init" in ctx


def test_context_silent_on_empty_dir(tmp_path):
    assert hook.build_context(str(tmp_path)) == ""


def test_script_failsafe_on_broken_state(tmp_path):
    claude = tmp_path / ".claude"; claude.mkdir()
    (claude / "project-state.json").write_text("{ this is not valid json")
    r = subprocess.run([sys.executable, os.path.join(REPO, "pw", "hook_sessionstart.py")],
                       capture_output=True, text=True, cwd=str(tmp_path))
    assert r.returncode == 0
    assert "Traceback" not in r.stderr
    assert "ModuleNotFoundError" not in r.stderr
    assert r.stdout.strip() == ""  # 깨진 상태 → 조용히 무출력


def test_script_emits_valid_json_when_initialized(tmp_path):
    d = _init(tmp_path)
    r = subprocess.run([sys.executable, os.path.join(REPO, "pw", "hook_sessionstart.py")],
                       capture_output=True, text=True, cwd=d)
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "backend-api" in payload["hookSpecificOutput"]["additionalContext"]

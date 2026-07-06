import json, os
from pw import cli

PRESETS = os.path.join(os.path.dirname(__file__), "..", "pw", "presets.json")

def _installed(tmp_path):
    slugs = ["context7@claude-plugins-official", "superpowers@superpowers-dev",
             "agentmemory@agentmemory", "andrej-karpathy-skills@karpathy-skills"]
    p = tmp_path / "installed.json"
    p.write_text(json.dumps({"plugins": {s: [{}] for s in slugs}}))
    return str(p)

def test_phase_next_advances_and_returns_guidance(tmp_path):
    proj = tmp_path / "p"; proj.mkdir()
    cli.cmd_init(str(proj), "minimal", PRESETS, _installed(tmp_path), now="t")
    out = cli.cmd_phase_next(str(proj), now="2026-07-06T01:00:00Z")
    assert out["phase"] == "plan"
    assert out["atEnd"] is False
    assert "plan" in out["guidance"]
    st = json.loads((proj / ".claude" / "project-state.json").read_text())
    assert st["phase"] == "plan"

def test_status_returns_current(tmp_path):
    proj = tmp_path / "p2"; proj.mkdir()
    cli.cmd_init(str(proj), "minimal", PRESETS, _installed(tmp_path), now="t")
    s = cli.cmd_status(str(proj))
    assert s["preset"] == "minimal"
    assert s["phase"] == "brainstorm"

def test_status_uninitialized_raises(tmp_path):
    proj = tmp_path / "empty"; proj.mkdir()
    try:
        cli.cmd_status(str(proj)); assert False
    except RuntimeError as e:
        assert "not initialized" in str(e)

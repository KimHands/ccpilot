import json, os
from pw import cli

def _installed(tmp_path):
    slugs = ["context7@claude-plugins-official", "superpowers@superpowers-dev",
             "agentmemory@agentmemory", "andrej-karpathy-skills@karpathy-skills",
             "static-analysis@trailofbits", "kesekit@kesekit",
             "security-guidance@claude-plugins-official", "code-simplifier@claude-plugins-official",
             "understand-anything@understand-anything"]
    p = tmp_path / "installed.json"
    p.write_text(json.dumps({"plugins": {s: [{}] for s in slugs}}))
    return str(p)

PRESETS = os.path.join(os.path.dirname(__file__), "..", "pw", "presets.json")

def test_init_writes_files_and_denylists_non_preset(tmp_path):
    proj = tmp_path / "proj"; proj.mkdir()
    res = cli.cmd_init(str(proj), "security-audit", PRESETS, _installed(tmp_path),
                       now="2026-07-06T00:00:00Z")
    settings = json.loads((proj / ".claude" / "settings.json").read_text())
    ep = settings["enabledPlugins"]
    assert ep["static-analysis@trailofbits"] is True          # 프리셋
    assert ep["superpowers@superpowers-dev"] is True           # alwaysOn
    assert ep["context7@claude-plugins-official"] is False     # 非프리셋 → denylist
    assert (proj / ".claude" / "playbook.md").exists()
    state = json.loads((proj / ".claude" / "project-state.json").read_text())
    assert state["preset"] == "security-audit" and state["phase"] == "brainstorm"
    assert "playbook" in (proj / "CLAUDE.md").read_text()

def test_init_dry_run_writes_nothing(tmp_path):
    proj = tmp_path / "proj2"; proj.mkdir()
    res = cli.cmd_init(str(proj), "minimal", PRESETS, _installed(tmp_path),
                       now="t", dry_run=True)
    assert res["dryRun"] is True
    assert not (proj / ".claude").exists()

def test_init_refuses_reinit_without_force(tmp_path):
    proj = tmp_path / "proj3"; proj.mkdir()
    cli.cmd_init(str(proj), "minimal", PRESETS, _installed(tmp_path), now="t")
    try:
        cli.cmd_init(str(proj), "minimal", PRESETS, _installed(tmp_path), now="t")
        assert False, "should have raised"
    except RuntimeError as e:
        assert "already initialized" in str(e)

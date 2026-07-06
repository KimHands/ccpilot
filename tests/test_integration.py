import json, os
from pw import cli

PRESETS = os.path.join(os.path.dirname(__file__), "..", "pw", "presets.json")

def test_end_to_end_init_then_phase_next(tmp_path, monkeypatch):
    proj = tmp_path / "app"; proj.mkdir()
    (proj / "pyproject.toml").write_text("[project]\nname='x'")
    (proj / "svc.py").write_text("x=1")
    inst = tmp_path / "installed.json"
    slugs = ["context7@claude-plugins-official", "superpowers@superpowers-dev",
             "agentmemory@agentmemory", "andrej-karpathy-skills@karpathy-skills",
             "pyright-lsp@claude-plugins-official"]
    inst.write_text(json.dumps({"plugins": {s: [{}] for s in slugs}}))
    res = cli.cmd_init(str(proj), "minimal", PRESETS, str(inst), now="t")
    # 언어 감지로 pyright LSP 가 활성에 포함
    assert "pyright-lsp@claude-plugins-official" in res["enabled"]
    pb = (proj / ".claude" / "playbook.md").read_text()
    assert "pyright-lsp" in pb
    out = cli.cmd_phase_next(str(proj), now="t2")
    assert out["phase"] == "plan"

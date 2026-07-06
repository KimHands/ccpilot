import os, sys, subprocess, json
from pw_route import cli

RULES = os.path.join(os.path.dirname(__file__), "..", "pw_route", "route-rules.json")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_route_security_available(tmp_path):
    agents = tmp_path / "agents"; agents.mkdir()
    (agents / "security-auditor.md").write_text("---\nname: security-auditor\n---\nx")
    ctx = cli.route("보안 점검해줘", RULES, [str(agents)])
    assert ctx["domain"] == "security"
    assert ctx["prefer"] == {"name": "security-auditor", "available": True}
    assert "security-auditor" in ctx["availableAgents"]

def test_route_unavailable_adds_restart_note(tmp_path):
    agents = tmp_path / "agents"; agents.mkdir()  # empty → security-auditor absent
    ctx = cli.route("보안 취약점 semgrep 스캔", RULES, [str(agents)])
    assert ctx["prefer"] == {"name": "security-auditor", "available": False}
    assert "restart" in ctx["note"].lower()

def test_default_agent_dirs_filters_existing(tmp_path):
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    dirs = cli.default_agent_dirs(str(tmp_path), str(tmp_path))
    assert any(d.endswith("/.claude/agents") for d in dirs)

def test_cli_runs_as_script_without_import_error(tmp_path):
    # 설치 경로처럼 스크립트로 직접 실행 → 임포트 크래시 없어야 함
    r = subprocess.run([sys.executable, os.path.join(REPO, "pw_route", "cli.py")],
                       capture_output=True, text=True, cwd=str(tmp_path))
    assert "ModuleNotFoundError" not in r.stderr
    assert r.returncode == 2   # argparse: missing subcommand

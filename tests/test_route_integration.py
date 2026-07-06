import os, subprocess
from pw_route import cli

RULES = os.path.join(os.path.dirname(__file__), "..", "pw_route", "route-rules.json")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_end_to_end_route_with_real_specialist_agents(tmp_path):
    # 실제 저장소의 agents/ 를 조회 대상으로 사용 → security-auditor 존재 → prefer available
    agents_dir = os.path.join(REPO, "agents")
    ctx = cli.route("이 저장소 보안 감사", RULES, [agents_dir])
    assert ctx["domain"] == "security"
    assert ctx["prefer"] == {"name": "security-auditor", "available": True}
    assert ctx["note"] == ""   # 사용 가능하므로 재시작 안내 없음

def test_install_sh_syntax_ok():
    r = subprocess.run(["bash", "-n", os.path.join(REPO, "install.sh")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

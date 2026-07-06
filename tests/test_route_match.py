import os
from pw_route import rules

RULES = os.path.join(os.path.dirname(__file__), "..", "pw_route", "route-rules.json")

def test_match_security_prefer_available():
    doc = rules.load_rules(RULES)
    r = rules.match_task("이 코드 보안 점검해줘", doc, {"security-auditor"})
    assert r["matched"] is True
    assert r["domain"] == "security"
    assert r["prefer"] == {"name": "security-auditor", "available": True}
    assert r["narrow"] is None

def test_match_narrow_semgrep_unavailable():
    doc = rules.load_rules(RULES)
    r = rules.match_task("run a semgrep security scan", doc, {"security-auditor"})
    assert r["narrow"] == {"name": "semgrep-scanner", "available": False}

def test_no_match_returns_fallback():
    doc = rules.load_rules(RULES)
    r = rules.match_task("write me a poem", doc, set())
    assert r["matched"] is False
    assert r["prefer"] is None
    assert r["fallback"] == "prefer-original-plugin-agents"

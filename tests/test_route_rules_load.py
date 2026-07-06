import json, os, pytest
from pw_route import rules

RULES = os.path.join(os.path.dirname(__file__), "..", "pw_route", "route-rules.json")

def test_load_rules_ok():
    d = rules.load_rules(RULES)
    assert d["schemaVersion"] == 1
    assert isinstance(d["rules"], list) and len(d["rules"]) >= 2
    assert d["fallback"] == "prefer-original-plugin-agents"
    assert any(r["domain"] == "security" for r in d["rules"])

def test_load_rules_bad_schema(tmp_path):
    p = tmp_path / "bad.json"; p.write_text(json.dumps({"schemaVersion": 2}))
    with pytest.raises(ValueError):
        rules.load_rules(str(p))

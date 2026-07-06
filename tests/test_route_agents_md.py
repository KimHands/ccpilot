import os

AGENTS = os.path.join(os.path.dirname(__file__), "..", "agents")
STRUCT_KEYS = ["findings", "evidence", "inspected", "confidence", "unresolved", "next"]

def _read(name):
    return open(os.path.join(AGENTS, name), encoding="utf-8").read()

def test_security_auditor_has_frontmatter_and_invariants():
    t = _read("security-auditor.md")
    assert t.startswith("---")
    assert "name: security-auditor" in t
    assert "수정하지 않는다" in t          # INV-1 (원본 미수정)
    for k in STRUCT_KEYS:
        assert k in t                        # 구조화 출력 계약
    assert "폴백" in t or "fallback" in t.lower()

def test_test_engineer_has_frontmatter_and_invariants():
    t = _read("test-engineer.md")
    assert t.startswith("---")
    assert "name: test-engineer" in t
    assert "수정하지 않는다" in t
    for k in STRUCT_KEYS:
        assert k in t

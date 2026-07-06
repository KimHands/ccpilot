from pw import state

PHASES = ["brainstorm", "plan", "implement"]

def test_default_state():
    s = state.default_state("web", PHASES, ["python"])
    assert s["schemaVersion"] == 1
    assert s["preset"] == "web"
    assert s["phase"] == "brainstorm"
    assert s["phases"] == PHASES
    assert s["detectedLanguages"] == ["python"]
    assert s["history"] == []

def test_advance_moves_to_next_and_records_history():
    s = state.default_state("web", PHASES, [])
    s2 = state.advance(s, now="2026-07-06T00:00:00Z")
    assert s2["phase"] == "plan"
    assert s2["history"][-1] == {"phase": "plan", "at": "2026-07-06T00:00:00Z"}
    assert "_atEnd" not in s2

def test_advance_at_last_phase_flags_end():
    s = state.default_state("web", PHASES, [])
    s["phase"] = "implement"
    s2 = state.advance(s, now="t")
    assert s2["phase"] == "implement"
    assert s2["_atEnd"] is True

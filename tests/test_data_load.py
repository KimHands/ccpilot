import json, os, pytest
from pw import data

PRESETS = os.path.join(os.path.dirname(__file__), "..", "pw", "presets.json")

def test_load_presets_returns_dict_with_required_keys():
    d = data.load_presets(PRESETS)
    assert d["schemaVersion"] == 1
    for key in ("alwaysOn", "phaseModel", "capabilityTags", "presets", "invocationRules"):
        assert key in d
    assert d["phaseModel"]["phases"] == ["brainstorm", "plan", "implement", "review", "ship"]

def test_load_presets_rejects_wrong_schema(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"schemaVersion": 99}))
    with pytest.raises(ValueError):
        data.load_presets(str(p))

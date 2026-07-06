import json
from pw import data

def test_installed_plugins_reads_keys(tmp_path):
    p = tmp_path / "installed.json"
    p.write_text(json.dumps({"plugins": {"a@m1": [{}], "b@m2": [{}]}}))
    assert data.installed_plugins(str(p)) == {"a@m1", "b@m2"}

def test_validate_slugs_splits_valid_and_missing():
    installed = {"context7@claude-plugins-official", "kesekit@kesekit"}
    valid, missing = data.validate_slugs(
        ["context7@claude-plugins-official", "ghost@nowhere", "kesekit@kesekit"], installed)
    assert valid == ["context7@claude-plugins-official", "kesekit@kesekit"]
    assert missing == ["ghost@nowhere"]

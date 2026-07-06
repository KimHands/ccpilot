import json
from pw import install_hook


def _settings_with_stop(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({"hooks": {"Stop": [
        {"hooks": [{"type": "command", "command": "afplay glass.aiff", "async": True}]}]}}))
    return str(p)


def test_ensure_hook_adds_and_preserves_existing(tmp_path):
    path = _settings_with_stop(tmp_path)
    assert install_hook.ensure_hook(path) == "added"
    d = json.loads(open(path).read())
    # Stop 보존
    assert d["hooks"]["Stop"][0]["hooks"][0]["command"] == "afplay glass.aiff"
    # SessionStart 추가됨, 우리 스크립트 참조
    cmds = [h["command"] for g in d["hooks"]["SessionStart"] for h in g["hooks"]]
    assert any("hook_sessionstart.py" in c for c in cmds)


def test_ensure_hook_idempotent(tmp_path):
    path = _settings_with_stop(tmp_path)
    install_hook.ensure_hook(path)
    assert install_hook.ensure_hook(path) == "present"
    d = json.loads(open(path).read())
    cmds = [h["command"] for g in d["hooks"]["SessionStart"] for h in g["hooks"]]
    assert sum("hook_sessionstart.py" in c for c in cmds) == 1  # 중복 없음


def test_ensure_hook_creates_settings_when_missing(tmp_path):
    path = str(tmp_path / "new.json")
    assert install_hook.ensure_hook(path) == "added"
    d = json.loads(open(path).read())
    assert "SessionStart" in d["hooks"]

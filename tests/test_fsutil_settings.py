from pw import fsutil

def test_merge_preserves_other_keys_and_sets_flags():
    existing = {"permissions": {"allow": ["x"]},
                "enabledPlugins": {"keep@m": True, "context7@cpo": True}}
    out = fsutil.merge_enabled_plugins(
        existing,
        enable=["a@m", "b@m"],
        disable=["context7@cpo", "c@m"])
    assert out["permissions"] == {"allow": ["x"]}          # 보존
    assert out["enabledPlugins"]["a@m"] is True
    assert out["enabledPlugins"]["b@m"] is True
    assert out["enabledPlugins"]["context7@cpo"] is False   # denylist가 덮어씀
    assert out["enabledPlugins"]["c@m"] is False
    assert out["enabledPlugins"]["keep@m"] is True          # 기존 유지

def test_enable_wins_over_disable():
    out = fsutil.merge_enabled_plugins({}, enable=["a@m"], disable=["a@m"])
    assert out["enabledPlugins"]["a@m"] is True

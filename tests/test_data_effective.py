import pytest
from pw import data

PRESETS = {"web": {"plugins": ["a@m", "b@m"]},
           "min": {"plugins": ["a@m"], "lspByLanguage": True}}
ALWAYS = ["sp@dev", "am@am"]

def test_plugin_name():
    assert data.plugin_name("context7@claude-plugins-official") == "context7"

def test_effective_dedup_and_order():
    eff = data.effective_plugins(PRESETS, "web", ALWAYS, lsp_slugs=["ts@cpo"])
    assert eff == ["a@m", "b@m", "sp@dev", "am@am"]   # web 은 lspByLanguage 아님 → lsp 제외

def test_effective_includes_lsp_when_flagged():
    eff = data.effective_plugins(PRESETS, "min", ALWAYS, lsp_slugs=["ts@cpo", "py@cpo"])
    assert eff == ["a@m", "sp@dev", "am@am", "ts@cpo", "py@cpo"]

def test_unknown_preset_raises():
    with pytest.raises(KeyError):
        data.effective_plugins(PRESETS, "ghost", ALWAYS, lsp_slugs=[])

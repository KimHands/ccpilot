from pw import playbook

PHASE_MODEL = {
    "phases": ["brainstorm", "implement", "review"],
    "roles": {
        "brainstorm": [
            {"role": "설계", "tool": "superpowers:brainstorming"},
            {"role": "기존코드", "tool": "understand-anything", "whenCapability": "existing-code"},
        ],
        "implement": [
            {"role": "LSP", "tool": "__lsp_by_language__"},
            {"role": "테스트", "tool": "test-writer-fixer"},
            {"role": "UI", "tool": "frontend-design", "whenCapability": "frontend"},
        ],
        "review": [{"role": "주력", "tool": "/code-review"}],
    },
}
RULES = {"orchestrator": {"primary": "superpowers", "rescueOnly": ["codex"]},
         "memory": {"single": "agentmemory"}}

def test_playbook_includes_available_excludes_missing():
    md = playbook.generate_playbook(
        preset_name="backend-api",
        phase_model=PHASE_MODEL,
        effective_slugs=["test-writer-fixer@awesome-claude-plugins", "superpowers@superpowers-dev"],
        capabilities=set(),                 # existing-code, frontend 없음
        lsp_slugs=["pyright-lsp@claude-plugins-official"],
        invocation_rules=RULES)
    assert md.startswith("<!-- pw:begin")
    assert md.rstrip().endswith("<!-- pw:end -->")
    assert "superpowers:brainstorming" in md          # builtin
    assert "understand-anything" not in md            # capability 없음
    assert "pyright-lsp" in md                        # LSP 확장
    assert "test-writer-fixer" in md                  # effective 에 있음
    assert "frontend-design" not in md                # frontend capability 없음
    assert "/code-review" in md
    assert "superpowers" in md and "codex" in md      # 호출 규칙 섹션

def test_playbook_omits_lsp_line_when_no_lsp():
    md = playbook.generate_playbook("minimal", PHASE_MODEL,
        effective_slugs=[], capabilities=set(), lsp_slugs=[], invocation_rules=RULES)
    assert "__lsp_by_language__" not in md

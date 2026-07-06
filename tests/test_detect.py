from pw import detect

TAGS = {"typescript": ["package.json", "tsconfig.json"],
        "python": ["pyproject.toml"],
        "frontend": ["package.json::react"],
        "infra": ["*.tf"]}
LSP_FOR = {"typescript": "typescript-lsp@cpo", "python": "pyright-lsp@cpo"}

def test_detects_file_and_content_and_glob(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies":{"react":"^18"}}')
    (tmp_path / "main.tf").write_text("resource {}")
    (tmp_path / "app.py").write_text("x=1")
    caps = detect.detect_capabilities(str(tmp_path), TAGS)
    assert "typescript" in caps      # package.json 존재
    assert "frontend" in caps        # react 포함
    assert "infra" in caps           # *.tf
    assert "existing-code" in caps    # app.py
    assert "python" not in caps       # pyproject.toml 없음

def test_lsp_slugs_maps_detected_languages():
    caps = {"typescript", "frontend"}
    assert detect.lsp_slugs(caps, LSP_FOR) == ["typescript-lsp@cpo"]

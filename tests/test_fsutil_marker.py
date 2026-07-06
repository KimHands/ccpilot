from pw import fsutil

BEGIN, END = "<!-- pw:begin -->", "<!-- pw:end -->"

def test_upsert_appends_when_no_marker():
    out = fsutil.upsert_marker_block("existing content\n", "NEW", BEGIN, END)
    assert "existing content" in out
    assert f"{BEGIN}\nNEW\n{END}" in out

def test_upsert_replaces_between_markers_preserving_outside():
    text = f"top\n{BEGIN}\nOLD\n{END}\nbottom\n"
    out = fsutil.upsert_marker_block(text, "NEW", BEGIN, END)
    assert "OLD" not in out
    assert "NEW" in out
    assert out.startswith("top")
    assert out.rstrip().endswith("bottom")

def test_read_json_default(tmp_path):
    assert fsutil.read_json(str(tmp_path / "none.json"), default={"x": 1}) == {"x": 1}

def test_upsert_handles_backslash_content():
    block = "C:\\Users\\x and \\1"

    # Append case (no existing markers)
    out_append = fsutil.upsert_marker_block("top\n", block, BEGIN, END)
    assert block in out_append

    # Replace case (markers already present)
    text = f"top\n{BEGIN}\nOLD\n{END}\nbottom\n"
    out_replace = fsutil.upsert_marker_block(text, block, BEGIN, END)
    assert block in out_replace
    assert "OLD" not in out_replace

def test_upsert_append_no_trailing_newline():
    out = fsutil.upsert_marker_block("nonl", "NEW", BEGIN, END)
    assert "nonl\n\n<!-- pw:begin -->" in out

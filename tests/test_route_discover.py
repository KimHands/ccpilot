from pw_route import discover

FM = """---
name: security-auditor
description: >-
  Audits security across tools.
tools: Bash, Read, Glob
---
body here
"""

def test_parse_frontmatter():
    d = discover.parse_frontmatter(FM)
    assert d["name"] == "security-auditor"
    assert d["tools"] == "Bash, Read, Glob"

def test_parse_frontmatter_none():
    assert discover.parse_frontmatter("no frontmatter here") == {}

def test_discover_agents_reads_dir(tmp_path):
    (tmp_path / "a.md").write_text("---\nname: alpha\ntools: Read\n---\nx")
    (tmp_path / "b.md").write_text("---\nname: beta\n---\ny")
    (tmp_path / "note.txt").write_text("ignored")
    agents = discover.discover_agents([str(tmp_path)])
    names = sorted(a["name"] for a in agents)
    assert names == ["alpha", "beta"]
    assert all("path" in a and "source" in a for a in agents)

def test_discover_dedup_first_wins(tmp_path):
    d1 = tmp_path / "d1"; d1.mkdir(); (d1 / "a.md").write_text("---\nname: dup\n---\n1")
    d2 = tmp_path / "d2"; d2.mkdir(); (d2 / "a.md").write_text("---\nname: dup\n---\n2")
    agents = discover.discover_agents([str(d1), str(d2)])
    assert len([a for a in agents if a["name"] == "dup"]) == 1
    assert agents[0]["source"] == str(d1)

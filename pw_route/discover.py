import os, glob

def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    out = {}
    for line in block.splitlines():
        if ":" not in line or line[:1] in (" ", "\t"):
            continue  # skip indented continuation / folded lines
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith((">", "|")):
            val = ""  # folded/literal scalar: value is on following indented lines
        if key in ("name", "description", "tools"):
            out[key] = val
    return out

def discover_agents(dirs):
    seen, result = set(), []
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "*.md"))):
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            fm = parse_frontmatter(text)
            name = fm.get("name")
            if not name or name in seen:
                continue
            seen.add(name)
            result.append({"name": name, "description": fm.get("description", ""),
                           "tools": fm.get("tools", ""), "path": path, "source": d})
    return result

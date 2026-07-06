import os, glob

SOURCE_EXTS = (".py", ".ts", ".js", ".go", ".rs")
IGNORE_DIRS = {".claude", "docs", "node_modules", ".git"}

def _marker_hit(project_dir, marker):
    if "::" in marker:
        fname, substr = marker.split("::", 1)
        p = os.path.join(project_dir, fname)
        return os.path.exists(p) and substr in open(p, encoding="utf-8", errors="ignore").read()
    if "*" in marker:
        return bool(glob.glob(os.path.join(project_dir, marker)))
    return os.path.exists(os.path.join(project_dir, marker))

def _has_source(project_dir):
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        if any(f.endswith(SOURCE_EXTS) for f in files):
            return True
    return False

def detect_capabilities(project_dir, capability_tags):
    caps = set()
    for cap, markers in capability_tags.items():
        if any(_marker_hit(project_dir, m) for m in markers):
            caps.add(cap)
    if _has_source(project_dir):
        caps.add("existing-code")
    return caps

def lsp_slugs(capabilities, lsp_for):
    return [slug for lang, slug in lsp_for.items() if lang in capabilities]

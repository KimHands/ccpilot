import argparse, os, re
from pw import data, detect, fsutil, playbook, state

CLAUDE_PTR = ("이 프로젝트는 .claude/playbook.md 의 단계별 워크플로우를 따른다. "
              "현재 단계는 .claude/project-state.json 참조.")
PTR_BEGIN, PTR_END = "<!-- pw:begin -->", "<!-- pw:end -->"

def _paths(project_dir):
    c = os.path.join(project_dir, ".claude")
    return {"claude": c,
            "settings": os.path.join(c, "settings.json"),
            "playbook": os.path.join(c, "playbook.md"),
            "state": os.path.join(c, "project-state.json"),
            "claudemd": os.path.join(project_dir, "CLAUDE.md")}

def cmd_init(project_dir, preset, presets_path, installed_path, now, dry_run=False, force=False):
    p = _paths(project_dir)
    if os.path.exists(p["state"]) and not force and not dry_run:
        raise RuntimeError("already initialized; use --repair or --force")
    presets = data.load_presets(presets_path)
    installed = data.installed_plugins(installed_path)
    caps = detect.detect_capabilities(project_dir, presets["capabilityTags"]["detect"])
    caps |= set(presets["presets"].get(preset, {}).get("capabilities", []))
    lsp = detect.lsp_slugs(caps, presets["capabilityTags"]["lspFor"])
    effective = data.effective_plugins(presets["presets"], preset, presets["alwaysOn"], lsp)
    enable, missing = data.validate_slugs(effective, installed)
    disable = [s for s in sorted(installed) if s not in set(enable)]
    pb = playbook.generate_playbook(preset, presets["phaseModel"], enable, caps, lsp,
                                    presets["invocationRules"])
    st = state.default_state(preset, presets["phaseModel"]["phases"], sorted(caps))
    result = {"enabled": enable, "disabled": disable, "missing": missing,
              "dryRun": dry_run, "written": []}
    if dry_run:
        return result
    settings = fsutil.merge_enabled_plugins(fsutil.read_json(p["settings"], {}), enable, disable)
    fsutil.write_json(p["settings"], settings)
    os.makedirs(p["claude"], exist_ok=True)
    with open(p["playbook"], "w", encoding="utf-8") as f:
        f.write(pb)
    fsutil.write_json(p["state"], st)
    existing_md = ""
    if os.path.exists(p["claudemd"]):
        existing_md = open(p["claudemd"], encoding="utf-8").read()
    with open(p["claudemd"], "w", encoding="utf-8") as f:
        f.write(fsutil.upsert_marker_block(existing_md, CLAUDE_PTR, PTR_BEGIN, PTR_END))
    result["written"] = [p["settings"], p["playbook"], p["state"], p["claudemd"]]
    return result

def _phase_section(playbook_text, phase):
    m = re.search(rf"(^## {re.escape(phase)}\b.*?)(?=^## |\Z)", playbook_text, re.DOTALL | re.MULTILINE)
    return m.group(1).strip() if m else ""

def cmd_phase_next(project_dir, now):
    p = _paths(project_dir)
    st = fsutil.read_json(p["state"])
    if st is None:
        raise RuntimeError("not initialized")
    st2 = state.advance(st, now)
    fsutil.write_json(p["state"], st2)
    pb = open(p["playbook"], encoding="utf-8").read() if os.path.exists(p["playbook"]) else ""
    return {"phase": st2["phase"], "atEnd": st2.get("_atEnd", False),
            "guidance": _phase_section(pb, st2["phase"])}

def cmd_status(project_dir):
    p = _paths(project_dir)
    st = fsutil.read_json(p["state"])
    if st is None:
        raise RuntimeError("not initialized")
    settings = fsutil.read_json(p["settings"], {})
    ep = settings.get("enabledPlugins", {})
    return {"preset": st["preset"], "phase": st["phase"],
            "enabled": [k for k, v in ep.items() if v],
            "disabled": [k for k, v in ep.items() if not v]}

def cmd_activate(project_dir, slug, installed_path):
    p = _paths(project_dir)
    installed = data.installed_plugins(installed_path)
    if slug not in installed:
        raise RuntimeError(f"not installed: {slug}")
    settings = fsutil.merge_enabled_plugins(fsutil.read_json(p["settings"], {}), [slug], [])
    fsutil.write_json(p["settings"], settings)
    return {"activated": slug, "note": "restart session to load"}

def main(argv):
    import datetime
    ap = argparse.ArgumentParser(prog="pw")
    sub = ap.add_subparsers(dest="cmd", required=True)
    home = os.path.expanduser("~")
    dflt_presets = os.path.join(home, ".claude", "project-presets.json")
    dflt_installed = os.path.join(home, ".claude", "plugins", "installed_plugins.json")
    pi = sub.add_parser("init"); pi.add_argument("preset"); pi.add_argument("--dry-run", action="store_true")
    pi.add_argument("--force", action="store_true")
    sub.add_parser("phase-next"); sub.add_parser("status")
    pa = sub.add_parser("activate"); pa.add_argument("slug")
    args = ap.parse_args(argv)
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    cwd = os.getcwd()
    if args.cmd == "init":
        out = cmd_init(cwd, args.preset, dflt_presets, dflt_installed, now,
                       dry_run=args.dry_run, force=args.force)
    elif args.cmd == "phase-next":
        out = cmd_phase_next(cwd, now)
    elif args.cmd == "status":
        out = cmd_status(cwd)
    elif args.cmd == "activate":
        out = cmd_activate(cwd, args.slug, dflt_installed)
    import json as _json
    print(_json.dumps(out, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))

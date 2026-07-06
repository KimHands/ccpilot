import os
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

from pw.data import plugin_name

BEGIN_TMPL = "<!-- pw:begin schemaVersion=1 preset={preset} -->"
END = "<!-- pw:end -->"
_ALWAYS_PREFIXES = ("superpowers:", "/code-review", "gh", "agentmemory:")

def _resolve(role, effective_names, capabilities, lsp_slugs):
    """이 역할이 플레이북에 포함되면 표시 문자열, 아니면 None."""
    if role.get("whenCapability") and role["whenCapability"] not in capabilities:
        return None
    tool = role["tool"]
    if tool == "__lsp_by_language__":
        names = [plugin_name(s) for s in lsp_slugs]
        return ", ".join(names) if names else None
    if tool.startswith(_ALWAYS_PREFIXES):
        return tool
    return tool if plugin_name(tool) in effective_names else None

def generate_playbook(preset_name, phase_model, effective_slugs, capabilities, lsp_slugs, invocation_rules):
    effective_names = {plugin_name(s) for s in effective_slugs}
    lines = [BEGIN_TMPL.format(preset=preset_name),
             f"# 프로젝트 플레이북 — {preset_name}",
             "> 현재 단계는 .claude/project-state.json. /phase-next 로 진행.", ""]
    for phase in phase_model["phases"]:
        lines.append(f"## {phase}")
        n = 1
        for role in phase_model["roles"].get(phase, []):
            shown = _resolve(role, effective_names, capabilities, lsp_slugs)
            if shown is not None:
                lines.append(f"{n}. {role['role']} — {shown}")
                n += 1
        if n == 1:
            lines.append("_(이 단계에 활성 도구 없음)_")
        lines.append("")
    orch = invocation_rules.get("orchestrator", {})
    mem = invocation_rules.get("memory", {})
    lines += ["## 호출 규칙 (충돌 가드)",
              f"- 오케스트레이터: {orch.get('primary')} 하나. {', '.join(orch.get('rescueOnly', []))} 는 rescue 시에만.",
              f"- 메모리: {mem.get('single')} 하나.",
              "- 리뷰: /code-review 주력 먼저 → 전문 리뷰어는 트리거 시 → 새 지적 없으면 정지.",
              END]
    return "\n".join(lines) + "\n"

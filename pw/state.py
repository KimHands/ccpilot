import copy

def default_state(preset, phases, detected_langs):
    return {"schemaVersion": 1, "preset": preset, "phase": phases[0],
            "phases": list(phases), "detectedLanguages": list(detected_langs), "history": []}

def advance(state, now):
    s = copy.deepcopy(state)
    phases = s["phases"]
    i = phases.index(s["phase"])
    if i >= len(phases) - 1:
        s["_atEnd"] = True
        return s
    s["phase"] = phases[i + 1]
    s.setdefault("history", []).append({"phase": s["phase"], "at": now})
    return s

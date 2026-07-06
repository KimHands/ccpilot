import json

REQUIRED_KEYS = ("alwaysOn", "phaseModel", "capabilityTags", "presets", "invocationRules")

def load_presets(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("schemaVersion") != 1:
        raise ValueError(f"unsupported schemaVersion: {d.get('schemaVersion')}")
    for k in REQUIRED_KEYS:
        if k not in d:
            raise ValueError(f"missing key: {k}")
    return d

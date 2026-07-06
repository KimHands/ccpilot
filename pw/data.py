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

def installed_plugins(installed_json_path):
    with open(installed_json_path, encoding="utf-8") as f:
        d = json.load(f)
    return set(d.get("plugins", {}).keys())

def validate_slugs(slugs, installed):
    valid = [s for s in slugs if s in installed]
    missing = [s for s in slugs if s not in installed]
    return valid, missing

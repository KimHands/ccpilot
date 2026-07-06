import json

def load_rules(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("schemaVersion") != 1:
        raise ValueError(f"unsupported schemaVersion: {d.get('schemaVersion')}")
    for k in ("rules", "fallback"):
        if k not in d:
            raise ValueError(f"missing key: {k}")
    if not isinstance(d["rules"], list):
        raise ValueError("rules must be a list")
    return d

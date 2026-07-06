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

def _avail(name, available_names):
    return {"name": name, "available": name in available_names}

def match_task(task, rules_doc, available_names):
    t = (task or "").lower()
    result = {"domain": None, "prefer": None, "narrow": None,
              "fallback": rules_doc.get("fallback"), "matched": False}
    for rule in rules_doc.get("rules", []):
        if any(kw.lower() in t for kw in rule.get("match", [])):
            result["matched"] = True
            result["domain"] = rule.get("domain")
            if rule.get("prefer"):
                result["prefer"] = _avail(rule["prefer"], available_names)
            for n in rule.get("narrow", []):
                if all(kw.lower() in t for kw in n.get("when", [])):
                    result["narrow"] = _avail(n["use"], available_names)
                    break
            break
    return result

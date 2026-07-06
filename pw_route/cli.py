import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse, glob, json
from pw_route import discover, rules

RESTART_NOTE = "capability unavailable in this session; enable preset and restart (/project-activate)"

def default_agent_dirs(home, cwd):
    candidates = [os.path.join(cwd, ".claude", "agents"),
                  os.path.join(home, ".claude", "agents")]
    candidates += glob.glob(os.path.join(home, ".claude", "plugins", "cache", "*", "*", "*", "agents"))
    return [d for d in candidates if os.path.isdir(d)]

def route(task, rules_path, agent_dirs):
    agents = discover.discover_agents(agent_dirs)
    names = {a["name"] for a in agents}
    doc = rules.load_rules(rules_path)
    m = rules.match_task(task, doc, names)
    note = ""
    prefer_unavail = m["prefer"] and not m["prefer"]["available"]
    narrow_ok = m["narrow"] and m["narrow"]["available"]
    if prefer_unavail and not narrow_ok:
        note = RESTART_NOTE
    return {"task": task, "domain": m["domain"], "prefer": m["prefer"],
            "narrow": m["narrow"], "fallback": m["fallback"], "matched": m["matched"],
            "availableAgents": sorted(names), "note": note}

def main(argv):
    ap = argparse.ArgumentParser(prog="pw_route")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("route"); pr.add_argument("task")
    pr.add_argument("--rules", default=os.path.join(os.path.expanduser("~"), ".claude", "route-rules.json"))
    args = ap.parse_args(argv)
    home, cwd = os.path.expanduser("~"), os.getcwd()
    if args.cmd == "route":
        out = route(args.task, args.rules, default_agent_dirs(home, cwd))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

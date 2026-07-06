import json, os, re

def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

def upsert_marker_block(text, block, begin, end):
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    new_block = f"{begin}\n{block}\n{end}"
    if pattern.search(text):
        return pattern.sub(new_block, text)
    sep = "" if text.endswith("\n") or text == "" else "\n"
    return f"{text}{sep}\n{new_block}\n"

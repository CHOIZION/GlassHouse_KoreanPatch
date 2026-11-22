import json
import re

with open("g4_raw.json", "r", encoding="utf-8") as f:
    raw_items = json.load(f)

with open("dict_b1.json", "r", encoding="utf-8") as f:
    dict_b1 = json.load(f)

with open("dict_b2.json", "r", encoding="utf-8") as f:
    dict_b2 = json.load(f)

# Also load DICT_4A from build_g4_partA.py
import build_g4_partA
dict_4a = build_g4_partA.DICT_4A

# Merge master dict for Group 4
master_dict = {}
master_dict.update(dict_4a)
master_dict.update(dict_b1)
master_dict.update(dict_b2)

# Exclude Italian draft boards
italian_boards = {
    'EMMA_1', 'MAKENNA_2', 'MAKENNA_2_PRE', 'MAKENNA_3', 'MAKENNA_4L', 'Corwin_1'
}

en_g4_items = [it for it in raw_items if it['board'] not in italian_boards]
print(f"Total English Group 4 Elements: {len(en_g4_items)}")

def extract_code(s):
    match = re.search(r'(<pre><code>.*?</code></pre>)', s)
    code = match.group(1) if match else ""
    s_clean = re.sub(r'<pre><code>.*?</code></pre>', '', s).strip()
    return s_clean, code

def clean_p(s):
    s = re.sub(r'^<p>', '', s)
    s = re.sub(r'</p>$', '', s).strip()
    return s

def translate_str(s):
    if not s or not s.strip(): return s
    if s.strip() in ['<p></p>', '<p>“...”</p><p></p>', '<p>“...”</p>', '']:
        return s

    s_clean, code_part = extract_code(s)
    text = clean_p(s_clean)
    text = text.replace('&gt;', '>').replace('&lt;', '<')

    if text in master_dict:
        ko = master_dict[text]
        return f"<p>{ko}</p>{code_part}"

    norm = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    if norm in master_dict:
        ko = master_dict[norm]
        return f"<p>{ko}</p>{code_part}"

    tagless = re.sub(r'<[^>]+>', '', text).strip()
    if tagless in master_dict:
        ko = master_dict[tagless]
        return f"<p>{ko}</p>{code_part}"

    for k, v in master_dict.items():
        k_norm = k.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
        if norm == k_norm:
            return f"<p>{v}</p>{code_part}"
        if tagless == re.sub(r'<[^>]+>', '', k).strip():
            return f"<p>{v}</p>{code_part}"

    if text.startswith("[CHOICE_") or text.startswith("CHOICE_"):
        return f"<p>{text}</p>{code_part}"

    return None

trans_g4 = {}
missing = []

for it in en_g4_items:
    eid = it["id"]
    entry = {}
    if it.get("title"):
        ko_t = translate_str(it["title"])
        if ko_t: entry["title"] = ko_t
        else: missing.append((it["board"], eid, "title", it["title"]))
    if it.get("content"):
        ko_c = translate_str(it["content"])
        if ko_c: entry["content"] = ko_c
        else: missing.append((it["board"], eid, "content", it["content"]))
    if it.get("outputs"):
        entry["outputs"] = []
        for o in it["outputs"]:
            ko_o = translate_str(o)
            entry["outputs"].append(ko_o if ko_o else o)
            if not ko_o and o.strip() and o.strip() not in ['<p></p>', '']:
                missing.append((it["board"], eid, "output", o))

    trans_g4[eid] = entry

print(f"Verified G4 English Elements: {len(trans_g4)}")
print(f"Missing count: {len(missing)}")
if missing:
    for m in missing[:25]:
        print(f"  MISSING [{m[0]}] {m[1]} ({m[2]}): {repr(m[3])}")

with open("trans_group4_verified.json", "w", encoding="utf-8") as f:
    json.dump(trans_g4, f, ensure_ascii=False, indent=2)

print("Saved trans_group4_verified.json successfully!")

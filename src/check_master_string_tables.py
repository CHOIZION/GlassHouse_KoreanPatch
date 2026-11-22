import json
import sys
import os

sys.path.append(r"C:\Users\czion\.gemini\antigravity\brain\e86e2b8e-9659-45ee-bfe4-8c0bc58b4084\scratch")
from trans_part1 import translations as t1
from trans_part2 import translations as t2
from trans_library import translations as t3
from verify_codex import codex_full as t4

master_translations = {}
for k, v in t1.items():
    master_translations[k] = v
for k, v in t2.items():
    master_translations[k] = v
for k, v in t3.items():
    master_translations[k] = v
master_translations["Codex_en"] = t4

print("Tables in master_translations:", len(master_translations))
total = 0
for k, v in master_translations.items():
    print(f"  {k}: {len(v)} entries")
    total += len(v)
print("Total entries:", total)

# Check against extracted JSON files
tables_dir = r"C:\Users\czion\.gemini\antigravity\brain\e86e2b8e-9659-45ee-bfe4-8c0bc58b4084\scratch\extracted_string_tables"
total_raw = 0
for fname in os.listdir(tables_dir):
    tname = fname.replace(".json", "")
    with open(os.path.join(tables_dir, fname), "r", encoding="utf-8") as f:
        data = json.load(f)
    total_raw += len(data)
    if tname in master_translations:
        matched = sum(1 for item in data if item["id"] in master_translations[tname])
        if matched != len(data):
            print(f"MISMATCH in {tname}: {matched}/{len(data)}")
    else:
        print(f"MISSING TABLE in master: {tname}")

print(f"Total raw: {total_raw}, Total translated: {total}")

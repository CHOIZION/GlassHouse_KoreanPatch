import UnityPy
from UnityPy.helpers import TypeTreeHelper
import json
import os
import re

# 1. Update check_master_string_tables.py fixes
scratch_dir = r"C:\Users\czion\.gemini\antigravity\brain\e86e2b8e-9659-45ee-bfe4-8c0bc58b4084\scratch"
game_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Glasshouse - Concept Demo\Glasshouse_Data\StreamingAssets\aa"
aa_windows = os.path.join(game_dir, "StandaloneWindows64")

str_bundle_path = os.path.join(aa_windows, "localization-string-tables-english(en)_assets_all.bundle")
assets_bundle_path = os.path.join(aa_windows, "localization-assets-english(en)_assets_all.bundle")
catalog_path = os.path.join(game_dir, "catalog.bin")

import sys
sys.path.append(scratch_dir)
from check_master_string_tables import master_translations

# Apply String Table Fixes
# Health and Threat back to English abbreviations
master_translations['UIElements_en'][13098330035929088] = 'HP'
master_translations['UIElements_en'][13098330035929089] = 'TH'

# V-Sync: remove parenthesis
master_translations['UIElements_en'][666789087363072] = '수직동기화'

# Tutorials tone fix: '동지들이여' -> '동지 여러분'
master_translations['Tutorials_en'][1557240396988436] = (
    '동지 여러분, 글래스하우스의 세계에 오신 것을 환영합니다.\n'
    '이동 가능한 지면을 <b>좌클릭</b>하여 탐험을 시작하십시오.'
)
master_translations['Tutorials_en'][89510122919903232] = (
    '동지 여러분, 글래스하우스의 세계에 오신 것을 환영합니다.\n'
    '<b>왼쪽 스틱</b>을 움직여 탐험을 시작하십시오.'
)

print("Applied fixes to master_translations!")

# 2. Inject String Tables Bundle
print("Injecting string tables bundle...")
str_bak = str_bundle_path + ".bak"
env_str = UnityPy.load(str_bak)

updated_str_count = 0
for obj in env_str.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        tname = tree.get("m_Name", "")
        if tname in master_translations:
            tdict = master_translations[tname]
            for it in tree.get("m_TableData", []):
                mid = it.get("m_Id")
                if mid in tdict:
                    it["m_Localized"] = tdict[mid]
                    updated_str_count += 1
            obj.save_typetree(tree)

str_out = env_str.file.save()
with open(str_bundle_path, "wb") as f:
    f.write(str_out)
print(f"Successfully saved {str_bundle_path} ({len(str_out)} bytes, {updated_str_count} entries)!")

# 3. Update Arcweave Translations
with open('master_arcweave_translations.json', 'r', encoding='utf-8') as f:
    master_arcweave = json.load(f)

# Fix 6 dialogue occurrences of 하오체
ha_o_fixes = {
    '99809336-454d-425e-8dd0-01b0ae03c6fd': {
        'content': '<p>"하지만 솔직히 말해서, 난 생-생식기가 훨씬 조-좋아. 놀랍거든. 잉크 두 자루를 하나에 품고 있는 셈이니까!"</p>'
    },
    'b8a5915f-2018-4644-a293-86f3e507961e': {
        'content': '<p>"환영하네, 이방인들이여."</p>'
    },
    '5739cc00-054a-4523-85e8-b56146a05237': {
        'content': '<p>"이 곡이 선사하는 다채로운 해석의 여지를 두 분 다 깊이 음미하시리라 믿네."</p>'
    },
    '0a881bda-1e41-4c0b-9f48-9f9a3e778fa5': {
        'content': '<p>"환영하네, 동무들!"</p>'
    },
    'c6313559-78ff-4c7b-b4cb-5e0d978dee8a': {
        'content': '<p>"환영하네, 동무들!"</p>'
    },
    'f17d07f4-8a3d-426d-90a4-d5482467ce65': {
        'content': '<p>"환영하네, 이방인들이여."</p>'
    }
}

for eid, fix in ha_o_fixes.items():
    if eid in master_arcweave:
        for k, v in fix.items():
            master_arcweave[eid][k] = v
        print(f"Patched arcweave dialogue for {eid}")

with open('master_arcweave_translations.json', 'w', encoding='utf-8') as f:
    json.dump(master_arcweave, f, ensure_ascii=False, indent=2)

# 4. Inject Arcweave Bundle
orig_write_value = TypeTreeHelper.write_value
def patched_write_value(value, node, writer, config):
    align = TypeTreeHelper.metaflag_is_aligned(node.m_MetaFlag)
    func = TypeTreeHelper.FUNCTION_WRITE_MAP.get(node.m_Type)
    if func:
        value = func(writer, value)
    elif node.m_Type == "pair":
        patched_write_value(value[0], node.m_Children[0], writer, config)
        patched_write_value(value[1], node.m_Children[1], writer, config)
    elif node.m_Type == "ReferencedObject":
        for child in node.m_Children:
            if child.m_Type == "ReferencedObjectData":
                ref_type_nodes = TypeTreeHelper.get_ref_type_node(value, config.assetsfile)
                if ref_type_nodes is None or child.m_Name not in value:
                    continue
                patched_write_value(value[child.m_Name], ref_type_nodes, writer, config)
            else:
                if child.m_Name in value:
                    patched_write_value(value[child.m_Name], child, writer, config)
    elif node.m_Children and node.m_Children[0].m_Type == "Array":
        if TypeTreeHelper.metaflag_is_aligned(node.m_Children[0].m_MetaFlag):
            align = True
        writer.write_int(len(value))
        subtype = node.m_Children[0].m_Children[1]
        for sub_value in value:
            patched_write_value(sub_value, subtype, writer, config)
    else:
        if isinstance(value, dict):
            for child in node.m_Children:
                if child.m_Type == "ManagedReferencesRegistry":
                    if config.has_registry:
                        continue
                    else:
                        config = config.copy()
                        config.has_registry = True
                if child.m_Name in value:
                    patched_write_value(value[child.m_Name], child, writer, config)
        else:
            for child in node.m_Children:
                if child.m_Type == "ManagedReferencesRegistry":
                    if config.has_registry:
                        continue
                    else:
                        config = config.copy()
                        config.has_registry = True
                patched_write_value(getattr(value, child._clean_name), child, writer, config)
    if align:
        writer.align_stream()

TypeTreeHelper.write_value = patched_write_value

print("Injecting arcweave bundle...")
assets_bak = assets_bundle_path + ".bak"
env_assets = UnityPy.load(assets_bak)

for obj in env_assets.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "Glasshouse_EN":
            refs = tree.get("references", {}).get("RefIds", [])
            for r in refs:
                if r.get('type', {}).get('class') == 'Element':
                    data = r.get("data", {})
                    eid = data.get("<Id>k__BackingField")
                    if eid in master_arcweave:
                        tinfo = master_arcweave[eid]
                        if tinfo.get('title') is not None:
                            data["<Title>k__BackingField"] = tinfo['title']
                        if tinfo.get('content') is not None:
                            data["<RawContent>k__BackingField"] = tinfo['content']
                        if tinfo.get('outputs') is not None and isinstance(tinfo['outputs'], list):
                            elem_outs = data.get("<Outputs>k__BackingField", [])
                            trans_outs = tinfo['outputs']
                            if len(elem_outs) == len(trans_outs):
                                for i, out_obj in enumerate(elem_outs):
                                    if trans_outs[i]:
                                        out_obj["<RawLabel>k__BackingField"] = trans_outs[i]
                            else:
                                non_empty_elem_outs = [o for o in elem_outs if o.get("<RawLabel>k__BackingField", "").strip()]
                                non_empty_trans = [o for o in trans_outs if o and o.strip()]
                                if len(non_empty_elem_outs) == len(non_empty_trans):
                                    for i, out_obj in enumerate(non_empty_elem_outs):
                                        out_obj["<RawLabel>k__BackingField"] = non_empty_trans[i]
            obj.save_typetree(tree)

assets_out = env_assets.file.save()
with open(assets_bundle_path, "wb") as f:
    f.write(assets_out)
print(f"Successfully saved {assets_bundle_path} ({len(assets_out)} bytes)!")

# 5. Patch catalog.bin
print("Patching catalog.bin...")
with open(catalog_path, 'rb') as f:
    cat_data = bytearray(f.read())

matches = list(re.finditer(rb'localization-[a-z0-9_\-\(\)]+\.bundle', cat_data))
for m in matches:
    name = m.group().decode()
    if name in ['localization-string-tables-english(en)_assets_all.bundle', 'localization-assets-english(en)_assets_all.bundle']:
        pos = m.end()
        offset = pos + 16 + 4 + 32 + 8
        bf = os.path.join(aa_windows, name)
        ns = os.path.getsize(bf)
        cat_data[offset:offset+4] = (0).to_bytes(4, 'little')
        cat_data[offset+4:offset+8] = ns.to_bytes(4, 'little')
        print(f"  catalog.bin -> {name}: CRC=0, Size={ns}")

with open(catalog_path, 'wb') as f:
    f.write(cat_data)

print("\nALL FIXES APPLIED SUCCESSFULLY!")

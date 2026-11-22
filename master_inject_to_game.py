import UnityPy
from UnityPy.helpers import TypeTreeHelper
import json
import shutil
import sys
import os

# Patched write_value for ReferencedObject in UnityPy
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
    else:  # Class
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

game_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Glasshouse - Concept Demo\Glasshouse_Data\StreamingAssets\aa\StandaloneWindows64"
str_bundle_path = os.path.join(game_dir, "localization-string-tables-english(en)_assets_all.bundle")
assets_bundle_path = os.path.join(game_dir, "localization-assets-english(en)_assets_all.bundle")

# 1. Backups
str_bak = str_bundle_path + ".bak"
assets_bak = assets_bundle_path + ".bak"

if not os.path.exists(str_bak):
    print(f"Creating backup: {str_bak}")
    shutil.copy2(str_bundle_path, str_bak)
else:
    print(f"Backup already exists: {str_bak}")

if not os.path.exists(assets_bak):
    print(f"Creating backup: {assets_bak}")
    shutil.copy2(assets_bundle_path, assets_bak)
else:
    print(f"Backup already exists: {assets_bak}")

# 2. Inject String Tables
sys.path.append(r"C:\Users\czion\.gemini\antigravity\brain\e86e2b8e-9659-45ee-bfe4-8c0bc58b4084\scratch")
from check_master_string_tables import master_translations

print("\n--- INJECTING STRING TABLES ---")
env_str = UnityPy.load(str_bak)
str_updated = 0
for obj in env_str.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        table_name = tree.get("m_Name", "")
        if table_name in master_translations:
            table_dict = master_translations[table_name]
            for item in tree.get("m_TableData", []):
                mid = item.get("m_Id")
                if mid in table_dict:
                    item["m_Localized"] = table_dict[mid]
                    str_updated += 1
            obj.save_typetree(tree)

str_out_bytes = env_str.file.save()
with open(str_bundle_path, "wb") as f:
    f.write(str_out_bytes)
print(f"Successfully injected {str_updated} string table entries into game bundle!")

# 3. Inject Arcweave Dialogue
print("\n--- INJECTING ARCWEAVE DIALOGUES ---")
with open('master_arcweave_translations.json', 'r', encoding='utf-8') as f:
    master_arcweave = json.load(f)

env_assets = UnityPy.load(assets_bak)
updated_elements = 0
updated_titles = 0
updated_contents = 0
updated_outputs = 0

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
                        changed = False
                        
                        # Title
                        if tinfo.get('title') is not None:
                            data["<Title>k__BackingField"] = tinfo['title']
                            updated_titles += 1
                            changed = True
                            
                        # Content
                        if tinfo.get('content') is not None:
                            data["<RawContent>k__BackingField"] = tinfo['content']
                            updated_contents += 1
                            changed = True
                            
                        # Outputs
                        if tinfo.get('outputs') is not None and isinstance(tinfo['outputs'], list):
                            elem_outs = data.get("<Outputs>k__BackingField", [])
                            trans_outs = tinfo['outputs']
                            if len(elem_outs) == len(trans_outs):
                                for i, out_obj in enumerate(elem_outs):
                                    if trans_outs[i]:
                                        out_obj["<RawLabel>k__BackingField"] = trans_outs[i]
                                        updated_outputs += 1
                                        changed = True
                            else:
                                non_empty_elem_outs = [o for o in elem_outs if o.get("<RawLabel>k__BackingField", "").strip()]
                                non_empty_trans = [o for o in trans_outs if o and o.strip()]
                                if len(non_empty_elem_outs) == len(non_empty_trans):
                                    for i, out_obj in enumerate(non_empty_elem_outs):
                                        out_obj["<RawLabel>k__BackingField"] = non_empty_trans[i]
                                        updated_outputs += 1
                                        changed = True

                        if changed:
                            updated_elements += 1
            
            print(f"Arcweave patch stats: {updated_elements} elements modified.")
            print(f"Titles: {updated_titles}, Contents: {updated_contents}, Outputs: {updated_outputs}")
            obj.save_typetree(tree)

print("Serializing and writing assets bundle directly to game directory...")
assets_out_bytes = env_assets.file.save()
with open(assets_bundle_path, "wb") as f:
    f.write(assets_out_bytes)
print(f"Successfully wrote {len(assets_out_bytes)} bytes to {assets_bundle_path}!")

# 4. Final In-Game Verification
print("\n--- FINAL VERIFICATION ON GAME BUNDLES ---")
# Verify String Tables
v_env_str = UnityPy.load(str_bundle_path)
v_str_count = 0
for obj in v_env_str.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        for item in tree.get("m_TableData", []):
            loc = item.get("m_Localized", "")
            if any('\uac00' <= ch <= '\ud7a3' for ch in loc):
                v_str_count += 1
print(f"String tables verification: {v_str_count} / {str_updated} entries contain Korean text.")

# Verify Arcweave
v_env_assets = UnityPy.load(assets_bundle_path)
v_arc_count = 0
sample_check = []
for obj in v_env_assets.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "Glasshouse_EN":
            refs = tree.get("references", {}).get("RefIds", [])
            for r in refs:
                if r.get('type', {}).get('class') == 'Element':
                    data = r.get("data", {})
                    c = data.get("<RawContent>k__BackingField", "")
                    t = data.get("<Title>k__BackingField", "")
                    if any('\uac00' <= ch <= '\ud7a3' for ch in (c + t)):
                        v_arc_count += 1
                        if len(sample_check) < 5 and c.strip():
                            sample_check.append((t, c[:80]))

print(f"Arcweave verification: {v_arc_count} elements contain Korean text.")
print("Sample Arcweave dialogues in game:")
for s in sample_check:
    print(f"  Title: {s[0]} | Content: {s[1]}")

print("\nALL INJECTIONS AND VERIFICATIONS COMPLETED SUCCESSFULLY!")

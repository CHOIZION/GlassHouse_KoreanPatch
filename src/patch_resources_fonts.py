import UnityPy
import os
import shutil

game_data = r"C:\Program Files (x86)\Steam\steamapps\common\Glasshouse - Concept Demo\Glasshouse_Data"
resources_path = os.path.join(game_data, "resources.assets")
resources_bak = resources_path + ".bak"

if not os.path.exists(resources_bak):
    print(f"Backing up resources.assets to {resources_bak}...")
    shutil.copy2(resources_path, resources_bak)
else:
    print(f"Backup already exists: {resources_bak}")

font_path = r"C:\Windows\Fonts\malgun.ttf"
with open(font_path, "rb") as f:
    ttf_bytes = f.read()

print(f"Loaded Korean font: {font_path} ({len(ttf_bytes)} bytes)")
pad_len = (4 - (len(ttf_bytes) % 4)) % 4
padded_ttf = ttf_bytes + b'\x00' * pad_len
new_len_bytes = len(ttf_bytes).to_bytes(4, 'little')

env = UnityPy.load(resources_bak)

target_font_pids = []
for obj in env.file.objects.values():
    if obj.type.name == "Font":
        try:
            data = obj.read()
            name = getattr(data, 'm_Name', '')
            if any(k in name for k in ['Cormorant', 'BKANT', 'bookantiqua', 'LiberationSans']):
                target_font_pids.append((obj.path_id, name, len(data.m_FontData)))
        except:
            pass

print(f"Found {len(target_font_pids)} target Font objects to patch:")
for pid, name, flen in target_font_pids:
    print(f"  Font {pid} ({name}): old len {flen}")

# Patch each target Font
for pid, name, flen in target_font_pids:
    obj = env.file.objects[pid]
    raw = obj.get_raw_data()
    old_len_bytes = flen.to_bytes(4, 'little')
    idx = raw.find(old_len_bytes)
    if idx == -1:
        print(f"  WARNING: Could not find font length offset for {name} ({pid})")
        continue
    
    header = raw[:idx]
    trailer = raw[idx + 4 + flen:]
    new_raw = header + new_len_bytes + padded_ttf + trailer
    obj.set_raw_data(new_raw)
    print(f"  Patched Font {pid} ({name}) -> new raw len: {len(new_raw)}")

print("Saving modified resources.assets...")
out_bytes = env.file.save()
with open(resources_path, "wb") as f:
    f.write(out_bytes)

print(f"Successfully wrote {len(out_bytes)} bytes to {resources_path}!")

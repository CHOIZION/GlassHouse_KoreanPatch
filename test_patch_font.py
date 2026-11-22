import UnityPy
import os

font_path = r"C:\Windows\Fonts\malgun.ttf"
with open(font_path, "rb") as f:
    ttf_bytes = f.read()

print(f"Loaded TTF font: {font_path} ({len(ttf_bytes)} bytes)")

scratch_test = r"C:\Users\czion\.gemini\antigravity\brain\e86e2b8e-9659-45ee-bfe4-8c0bc58b4084\scratch\test_sharedassets0.assets"
env = UnityPy.load(scratch_test)

# Check Font 128
obj = env.file.objects[128]
raw = obj.get_raw_data()
old_len = int.from_bytes(raw[76:80], 'little')
print(f"Font 128 old font len: {old_len}")

header = raw[:76]
trailer = raw[80 + old_len:]

# Build new raw
new_len_bytes = len(ttf_bytes).to_bytes(4, 'little')
# TTF bytes should be 4-byte aligned if needed
pad_len = (4 - (len(ttf_bytes) % 4)) % 4
padded_ttf = ttf_bytes + b'\x00' * pad_len

new_raw = header + new_len_bytes + padded_ttf + trailer
print(f"Font 128 new raw len: {len(new_raw)}")
obj.set_raw_data(new_raw)

# Also Font 129
obj2 = env.file.objects[129]
raw2 = obj2.get_raw_data()
old_len2 = int.from_bytes(raw2[84:88], 'little')
print(f"Font 129 old font len: {old_len2}")

header2 = raw2[:84]
trailer2 = raw2[88 + old_len2:]
new_raw2 = header2 + new_len_bytes + padded_ttf + trailer2
print(f"Font 129 new raw len: {len(new_raw2)}")
obj2.set_raw_data(new_raw2)

saved_bytes = env.file.save()
with open(scratch_test, "wb") as f:
    f.write(saved_bytes)

print(f"Saved modified test_sharedassets0.assets ({len(saved_bytes)} bytes)!")

# Reload and verify
env2 = UnityPy.load(scratch_test)
data128 = env2.file.objects[128].read()
print(f"Reload verification Font 128 font_data len: {len(data128.m_FontData)}")
data129 = env2.file.objects[129].read()
print(f"Reload verification Font 129 font_data len: {len(data129.m_FontData)}")

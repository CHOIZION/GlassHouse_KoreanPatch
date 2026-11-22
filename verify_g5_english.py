import json
import re

with open('dict_5a.json', 'r', encoding='utf-8') as f:
    dict_a = json.load(f)
with open('dict_5b.json', 'r', encoding='utf-8') as f:
    dict_b = json.load(f)
with open('dict_5c.json', 'r', encoding='utf-8') as f:
    dict_c = json.load(f)
with open('dict_5d.json', 'r', encoding='utf-8') as f:
    dict_d = json.load(f)

FIXUPS = {
    '"Forgive us. My husband\'s a bit of a nuisance once he\'s had a few drinks. You know what the <strong>Onion Festival</strong>\'s like."':
        '“용서해 주세요. 제 남편이 술만 몇 잔 들어가면 좀 성가시게 굴어서요. <strong>양파 축제</strong> 기간엔 다들 어떤지 아시잖아요.”',
    '{sprite name="con"} {sprite name="1"}"An enormous waste of paper. Those funds could be used for something far more worthwhile like REPAIRING THE DOCKING PIER."':
        '{sprite name="con"} {sprite name="1"}"막대한 종이 낭비야. 그 예산은 선착장 부두를 수리하는 것 같이 훨씬 더 가치 있는 일에 쓰일 수도 있었을 텐데 말이지."',
    '"Alright then. What\'s the plan?"':
        '“좋아, 그럼. 계획이 뭐야?”'
}

MASTER_G5 = {}
MASTER_G5.update(dict_a)
MASTER_G5.update(dict_b)
MASTER_G5.update(dict_c)
MASTER_G5.update(dict_d)
MASTER_G5.update(FIXUPS)

print(f"Total entries in MASTER_G5: {len(MASTER_G5)}")

with open('g5_raw.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

dev_design_boards = {'[DEMO-QD]', 'PROLOGUE - SUMMARY'}
playable_g5 = [it for it in items if it['board'] not in dev_design_boards]
print(f"Total playable items in Group 5: {len(playable_g5)}")

def translate_str(s):
    if not s:
        return s
    
    code_match = re.search(r'(<pre><code>.*?</code></pre>)', s, re.DOTALL)
    code_part = code_match.group(1) if code_match else ''
    
    s_clean = re.sub(r'<pre><code>.*?</code></pre>', '', s, flags=re.DOTALL).strip()
    
    has_p = s_clean.startswith('<p>') and s_clean.endswith('</p>')
    text = re.sub(r'^<p>', '', s_clean)
    text = re.sub(r'</p>$', '', text).strip()
    text = text.replace('&gt;', '>').replace('&lt;', '<')
    
    if not text or text in ['“...”', '""', '...']:
        return s
    
    if text.startswith('[CHOICE_') or text.startswith('CHOICE_'):
        return s

    if text in MASTER_G5:
        trans = MASTER_G5[text]
        res = f"<p>{trans}</p>" if has_p else trans
        if code_part:
            res = f"{code_part}\n{res}"
        return res
    
    return None

missing = []
verified_items = []

for item in playable_g5:
    new_item = dict(item)
    
    for fld in ['title', 'content']:
        v = item.get(fld)
        if v:
            t = translate_str(v)
            if t is None:
                missing.append((item['board'], fld, v))
            else:
                new_item[fld] = t
                
    if 'outputs' in item:
        new_outputs = []
        for o in item['outputs']:
            if o:
                t = translate_str(o)
                if t is None:
                    missing.append((item['board'], 'output', o))
                else:
                    new_outputs.append(t)
            else:
                new_outputs.append(o)
        new_item['outputs'] = new_outputs
        
    verified_items.append(new_item)

print(f"Group 5 verification complete: {len(verified_items)} items.")
print(f"Missing items count: {len(missing)}")

if missing:
    print("Samples of missing items:")
    for m in missing[:20]:
        print(f"Board: {m[0]}, Field: {m[1]}, Text: {repr(m[2])}")
else:
    with open('trans_group5_verified.json', 'w', encoding='utf-8') as f:
        json.dump(verified_items, f, ensure_ascii=False, indent=2)
    print("Saved trans_group5_verified.json successfully!")

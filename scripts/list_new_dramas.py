import re, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.parse_new_dramas import parsed_dramas

EXCLUDED_MSGS = {4049, 4590, 4591, 4592, 4593, 4594, 4595, 4596, 4597, 4598, 4599, 4600}

new_dramas = []
for d in parsed_dramas:
    # check if all episodes are in EXCLUDED_MSGS
    if all(m[1] in EXCLUDED_MSGS for m in d['episodes']):
        continue
    new_dramas.append(d)

print(f"Total new dramas to ingest: {len(new_dramas)}")
for idx, d in enumerate(new_dramas, start=351):
    print(f"[{idx}] {d['raw_title']} ({len(d['episodes'])} qism)")

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\Agent\Drama Bot')
from scripts.parse_new_dramas import parsed_dramas
from database import normalize_search_text

titles_map = {}
for idx, d in enumerate(parsed_dramas):
    norm = normalize_search_text(d['raw_title'])
    if norm in titles_map:
        titles_map[norm].append((idx, d['raw_title'], len(d['episodes']), d['episodes'][0][1], d['episodes'][-1][1]))
    else:
        titles_map[norm] = [(idx, d['raw_title'], len(d['episodes']), d['episodes'][0][1], d['episodes'][-1][1])]

print("Duplicated titles across the file:")
for norm, occurrences in titles_map.items():
    if len(occurrences) > 1:
        print(f"\nTitle: '{norm}' appeared {len(occurrences)} times:")
        for occ in occurrences:
            print(f"   Block #{occ[0]}: '{occ[1]}' ({occ[2]} eps, msgs: {occ[3]}..{occ[4]})")

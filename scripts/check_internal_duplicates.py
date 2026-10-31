import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.parse_new_dramas import parsed_dramas

EXCLUDED_MSGS = {4049, 4590, 4591, 4592, 4593, 4594, 4595, 4596, 4597, 4598, 4599, 4600}

new_dramas = []
for d in parsed_dramas:
    if all(m[1] in EXCLUDED_MSGS for m in d['episodes']):
        continue
    new_dramas.append(d)

print(f"Total raw items: {len(new_dramas)}")

# Check duplicate message IDs among new dramas
seen_msgs = {}
duplicate_blocks = []
for idx, d in enumerate(new_dramas):
    first_msg = d['episodes'][0][1]
    if first_msg in seen_msgs:
        prev_idx = seen_msgs[first_msg]
        duplicate_blocks.append((idx, d['raw_title'], prev_idx, new_dramas[prev_idx]['raw_title'], first_msg))
    else:
        seen_msgs[first_msg] = idx

print(f"Number of duplicate drama blocks in the user's file: {len(duplicate_blocks)}")
for curr_i, curr_t, prev_i, prev_t, msg in duplicate_blocks:
    print(f"Item #{curr_i} '{curr_t}' is duplicate of #{prev_i} '{prev_t}' (same start msg: {msg})")

import asyncio
import time
import sys
import difflib
import re
from functools import lru_cache
from collections import defaultdict

sys.path.insert(0, r"E:\Agent\Drama Bot")
import database

# Perfect Fast Match Engine with Candidate Pruning
UZBEK_SUFFIXES_SORTED = tuple(sorted(database.UZBEK_SUFFIXES, key=len, reverse=True))
UZBEK_NUM_PATTERNS = tuple([
    (re.compile(r"\b" + re.escape(phrase) + r"\b"), digit)
    for phrase, digit in sorted(database.UZBEK_NUM_WORDS.items(), key=lambda x: len(x[0]), reverse=True)
])

@lru_cache(maxsize=8192)
def fast_stem_uzbek_token(w: str) -> str:
    w = w.lower().strip()
    w = re.sub(r"[ʻʼ'\`’‘]", "", w)
    for sfx in UZBEK_SUFFIXES_SORTED:
        if w.endswith(sfx) and len(w) - len(sfx) >= 3:
            w = w[:-len(sfx)]
            break
    if len(w) >= 4 and w[-1] == w[-2]:
        w = w[:-1]
    return w

@lru_cache(maxsize=4096)
def fast_normalize_search_text(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"['`‘’ʻʼ]", "", text.lower())
    t = re.sub(r"[\-_/()[\].,:;!?+]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for pat, digit in UZBEK_NUM_PATTERNS:
        t = pat.sub(digit, t)
    return re.sub(r"\s+", " ", t).strip()

@lru_cache(maxsize=16384)
def fast_match_token_cached(qt: str, tt: str) -> float:
    if qt == tt:
        return 1.0

    qt_h = qt.replace('x', 'h')
    tt_h = tt.replace('x', 'h')
    if qt_h == tt_h:
        return 0.98

    qs = fast_stem_uzbek_token(qt)
    ts = fast_stem_uzbek_token(tt)
    if qs == ts:
        return 0.95
    if qs.replace('x', 'h') == ts.replace('x', 'h'):
        return 0.95

    lq, lt = len(qt), len(tt)
    if lq >= 2 and lt >= 2 and tt.startswith(qt):
        if lq / lt >= 0.5:
            return 0.85
    lqs, lts = len(qs), len(ts)
    if lqs >= 3 and lts >= 3 and ts.startswith(qs):
        return 0.90

    if lq >= 4 and lt >= 4:
        if qt_h[:4] == tt_h[:4]:
            r = difflib.SequenceMatcher(None, qt_h, tt_h).ratio()
            if r >= 0.65:
                return 0.85
        if abs(lq - lt) <= 2:
            r = difflib.SequenceMatcher(None, qt_h, tt_h).ratio()
            if r >= 0.75:
                return r * 0.90

    return 0.0

class FastSearchEngine:
    def __init__(self):
        self.items = []
        self.code_map = {}
        self.code_prefixes = defaultdict(set)
        self.query_cache = {}
        self.last_built = 0.0
        self._lock = asyncio.Lock()

    async def ensure_index(self):
        now = time.time()
        if self.items and (now - self.last_built < 300):
            return
        async with self._lock:
            if self.items and (time.time() - self.last_built < 300):
                return
            await self._build()

    async def _build(self):
        import aiosqlite
        async with aiosqlite.connect(database.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT id, code, title, slug, genre, year, poster_url, total_episodes, views, status, country, actors, aliases
                FROM doramas
            """) as cur:
                rows = [dict(r) for r in await cur.fetchall()]

        new_items = []
        new_code_map = {}
        new_code_prefixes = defaultdict(set)

        for idx, d in enumerate(rows):
            title = d.get("title") or ""
            aliases = d.get("aliases") or ""
            num_expanded = database.expand_digits_to_uzbek_words(f"{title} {aliases}")
            full_title_text = f"{title} {aliases} {num_expanded}".strip()
            t_clean = fast_normalize_search_text(full_title_text)
            t_clean_h = t_clean.replace("x", "h")
            t_tokens = tuple(t_clean.split())
            genre_clean = fast_normalize_search_text(d.get("genre") or "")
            code_str = str(d.get("code") or "")

            if code_str:
                new_code_map[code_str] = idx
                for l in range(1, len(code_str) + 1):
                    new_code_prefixes[code_str[:l]].add(idx)

            new_items.append({
                "idx": idx,
                "d": d,
                "code_str": code_str,
                "t_clean": t_clean,
                "t_clean_padded": f" {t_clean} ",
                "t_clean_h": t_clean_h,
                "t_clean_h_padded": f" {t_clean_h} ",
                "t_tokens": t_tokens,
                "genre_clean": genre_clean,
                "views": d.get("views", 0)
            })

        self.items = new_items
        self.code_map = new_code_map
        self.code_prefixes = new_code_prefixes
        self.query_cache.clear()
        self.last_built = time.time()

    def invalidate(self):
        self.last_built = 0.0
        self.query_cache.clear()

    async def search(self, query: str, limit: int = 10, offset: int = 0):
        q = (query or "").strip()
        if not q:
            return []
        if len(q) < 2 and not q.isdigit():
            return []

        await self.ensure_index()

        q_norm = fast_normalize_search_text(q)
        cache_key = (q_norm, limit, offset)
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]

        raw_tokens = tuple(q_norm.split())
        informative_tokens = tuple(w for w in raw_tokens if w not in database.COMMON_STOPWORDS)
        q_norm_h = q_norm.replace("x", "h")
        q_norm_padded = f" {q_norm} "
        q_norm_h_padded = f" {q_norm_h} "

        # Fast path for digit / code query
        if q_norm.isdigit():
            cand_indices = self.code_prefixes.get(q_norm)
            if cand_indices:
                target_items = [self.items[i] for i in cand_indices]
            else:
                target_items = self.items
        else:
            target_items = self.items

        scored_doramas = []
        for item in target_items:
            code_str = item["code_str"]
            t_clean = item["t_clean"]
            t_clean_padded = item["t_clean_padded"]
            t_clean_h_padded = item["t_clean_h_padded"]
            score = 0.0

            if q_norm == code_str:
                score = 100.0
            elif q_norm.isdigit() and code_str.startswith(q_norm):
                score = 85.0 + (len(q_norm) / len(code_str)) * 10.0
            elif q_norm == t_clean:
                score = 98.0
            elif t_clean.startswith(q_norm):
                score = 96.0
            elif len(q_norm) >= 4 and q_norm in t_clean:
                score = 90.0
            elif q_norm_padded in t_clean_padded:
                score = 92.0
            elif q_norm_h_padded in t_clean_h_padded:
                score = 91.0
            else:
                if raw_tokens and item["t_tokens"]:
                    total_token_score = 0.0
                    matched_informative = 0
                    matched_count = 0
                    t_toks = item["t_tokens"]

                    for qt in raw_tokens:
                        is_stop = qt in database.COMMON_STOPWORDS
                        best_match = 0.0
                        for tt in t_toks:
                            m = fast_match_token_cached(qt, tt)
                            if m > best_match:
                                best_match = m
                        if best_match > 0:
                            matched_count += 1
                            weight = 0.3 if is_stop else 1.0
                            total_token_score += best_match * weight
                            if not is_stop and best_match >= 0.65:
                                matched_informative += 1

                    if len(informative_tokens) <= 2:
                        min_req_informative = len(informative_tokens)
                    else:
                        min_req_informative = max(2, int(len(informative_tokens) * 0.67 + 0.5))

                    if informative_tokens and matched_informative < min_req_informative:
                        score = 0.0
                    elif not informative_tokens and matched_count == 0:
                        score = 0.0
                    else:
                        max_possible_weight = sum(0.3 if w in database.COMMON_STOPWORDS else 1.0 for w in raw_tokens)
                        ratio = total_token_score / max_possible_weight if max_possible_weight > 0 else 0
                        if matched_count == len(raw_tokens):
                            score = 80.0 + (ratio * 12.0)
                        elif ratio >= 0.5:
                            score = 45.0 + (ratio * 25.0)

            if score == 0.0 and item["genre_clean"] and q_norm in item["genre_clean"]:
                score = 35.0

            if score > 0:
                scored_doramas.append((score, item["views"], item["d"]))

        scored_doramas.sort(key=lambda x: (x[0], x[1]), reverse=True)
        if scored_doramas and scored_doramas[0][0] >= 80.0:
            best_score = scored_doramas[0][0]
            scored_doramas = [item for item in scored_doramas if item[0] >= max(50.0, best_score * 0.75)]

        res = [item[2] for item in scored_doramas][offset:offset + limit]
        if len(self.query_cache) > 1000:
            self.query_cache.clear()
        self.query_cache[cache_key] = res
        return res

async def main():
    engine = FastSearchEngine()
    await engine.ensure_index()

    test_queries = [
        "sevgi", "doktor", "101", "yolgon", "qirol", "qasosi", "hayot", "tibbiyot",
        "maktab", "qotil", "prokuror", "advokat", "oy", "yurak", "quvvatla", "522",
        "ruh", "rux", "baxt", "baht", "muhabbat", "muxabbat", "daha", "17", "oltin",
        "qayta turmush qurgan", "doktor x", "shifokor", "yoshlik", "qonun"
    ]

    t0 = time.perf_counter()
    for q in test_queries:
        res = await engine.search(q)
    t1 = time.perf_counter()
    print(f"Cold search: {(t1-t0)*1000:.2f}ms total across {len(test_queries)} queries (avg: {(t1-t0)*1000/len(test_queries):.2f}ms/query)")

    t0 = time.perf_counter()
    for q in test_queries:
        res = await engine.search(q)
    t1 = time.perf_counter()
    print(f"Cached search: {(t1-t0)*1000:.4f}ms total across {len(test_queries)} queries (avg: {(t1-t0)*1000/len(test_queries):.4f}ms/query)")

if __name__ == "__main__":
    asyncio.run(main())

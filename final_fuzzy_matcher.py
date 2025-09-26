# mapping demo using normalization, token overlap, surname weighting, and fuzzy fallback
import unicodedata, re
from difflib import SequenceMatcher
from rapidfuzz import fuzz


def load_csv(file_path):
    names = []
    with open(file_path, "r") as f:
        for line in f.readlines():
            names.append(line.strip())
    return names

# EPL_players = [
# "Igor Julio",
# "Hamed Traore",
# "Eli Kroupi",
# "Ben Gannon-Doak",
# "Hwang Hee-Chan",
# "Youssef Chermiti"
# ]

# fantasy_players = [
# "Mohamed Elyounoussi",
# "Mohamed Elneny",
# "Eli Junior Kroupi",
# "Ben Osborn",
# "Ben Mee",
# "Ben Godfrey",
# "Benjamin Fredrick",
# "Elijah Adebayo",
# "Ben Doak",
# "Ben Knight",
# "Hamed Junior Traore",
# "Hee-chan Hwang",
# "Ui-Jo Hwang",
# "Igor",
# "Igor Jesus",
# "Chermiti",
# "Kadan Young",
# "Ashley Young"
# ]

# try to use rapidfuzz if available for better fuzzy matching. Fallback to difflib.
try:
    def fuzzy_score(a, b):
        return fuzz.token_set_ratio(a, b)
    has_rapidfuzz = True
except Exception:
    def fuzzy_score(a, b):
        return int(SequenceMatcher(None, a, b).ratio() * 100)
    has_rapidfuzz = False

def normalize(name):
    s = name.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('-', ' ').replace('–', ' ').replace("’", "'")
    s = re.sub(r"[^a-z0-9'\s]", ' ', s)  # keep alphanum and apostrophes
    s = re.sub(r"\b(jr|junior)\b", '', s)  # drop junior/jr
    s = re.sub(r"\s+", ' ', s).strip()
    return s

def tokens(name):
    return [t for t in normalize(name).split() if len(t) > 0]

def token_overlap_score(a, b):
    A = set(tokens(a)); B = set(tokens(b))
    if not A or not B:
        return 0.0
    return 100.0 * (2 * len(A & B) / (len(A) + len(B)))

def surname(name):
    t = tokens(name)
    return t[-1] if t else ""

def match_score(a, b, weights=(0.4, 0.35, 0.25)):
    # weights: surname_match, token_overlap, fuzzy
    surname_match = 100.0 if surname(a) and surname(a) == surname(b) else 0.0
    t_overlap = token_overlap_score(a, b)
    fz = fuzzy_score(normalize(a), normalize(b))
    s = weights[0] * surname_match + weights[1] * t_overlap + weights[2] * fz
    return round(s, 2), round(surname_match,2), round(t_overlap,2), round(fz,2)

def candidate_block(epl_name, pool, min_shared_tokens=1):
    e_tokens = set(tokens(epl_name))
    candidates = [p for p in pool if e_tokens & set(tokens(p))]
    # if blocking returns nothing, relax to surname match or full pool
    if not candidates:
        s = surname(epl_name)
        if s:
            candidates = [p for p in pool if surname(p) == s]
    if not candidates:
        candidates = pool[:]
    return candidates

def map_players(epl_list, fantasy_list, threshold=70):
    results = []
    for e in epl_list:
        cands = candidate_block(e, fantasy_list)
        scored = []
        for f in cands:
            s, sm, to, fz = match_score(e, f)
            scored.append((f, s, sm, to, fz))
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:5]
        accepted = top[0] if top and top[0][1] >= threshold else None
        results.append({
            "epl": e,
            "best_match": accepted[0] if accepted else None,
            "best_score": accepted[1] if accepted else (top[0][1] if top else None),
            "candidates_top3": [{"name": t[0], "score": t[1], "surname_match": t[2], "token_overlap": t[3], "fuzzy": t[4]} for t in top[:3]]
        })
    return results


EPL_players = load_csv("epl_players_remained_after_second_iter.csv")
fantasy_players = load_csv("remaining_fantasy_display_names.csv")
mapping = map_players(EPL_players, fantasy_players, threshold=70)

# display results
for r in mapping:
    print("EPL:", r["epl"])
    print("  Best match:", r["best_match"], "Score:", r["best_score"])
    print("  Top candidates:")
    for c in r["candidates_top3"]:
        print("    -", c["name"], f"(score={c['score']}, surname_match={c['surname_match']}, token_overlap={c['token_overlap']}, fuzzy={c['fuzzy']})")
    print()

print("rapidfuzz available:", has_rapidfuzz)
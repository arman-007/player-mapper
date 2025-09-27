#!/usr/bin/env python3
"""
stage3_fuzzy.py

Fuzzy-matching stage with CLI threshold argument (default 70) and --dry-run flag.
- In dry-run mode the script does not modify output_files/individual_player.json.
- The script still writes intermediary_files/fuzzy_mapping_results.json and remaining_fantasy_display_names_after_fuzzy.csv
  so you can inspect what *would* be exported.
"""

import os
import json
import unicodedata
import re
import argparse
from difflib import SequenceMatcher

# Try to use rapidfuzz if available
try:
    from rapidfuzz import fuzz
    def fuzzy_score(a, b):
        return fuzz.token_set_ratio(a, b)
    has_rapidfuzz = True
except Exception:
    def fuzzy_score(a, b):
        return int(SequenceMatcher(None, a, b).ratio() * 100)
    has_rapidfuzz = False

# -----------------------------
# I/O helpers
# -----------------------------
def load_csv(file_path):
    names = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            val = line.strip()
            if val:
                names.append(val)
    return names

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# -----------------------------
# Normalization & token helpers
# -----------------------------
def normalize(name):
    s = (name or "").lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace('-', ' ').replace('–', ' ').replace("’", "'")
    s = re.sub(r"[^a-z0-9'\s]", ' ', s)
    s = re.sub(r"\b(jr|junior)\b", '', s)
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

# -----------------------------
# Scoring + blocking
# -----------------------------
def match_score(a, b, weights=(0.4, 0.35, 0.25)):
    surname_match = 100.0 if surname(a) and surname(a) == surname(b) else 0.0
    t_overlap = token_overlap_score(a, b)
    fz = fuzzy_score(normalize(a), normalize(b))
    s = weights[0] * surname_match + weights[1] * t_overlap + weights[2] * fz
    return round(s, 2), round(surname_match, 2), round(t_overlap, 2), round(fz, 2)

def candidate_block(epl_name, pool):
    e_tokens = set(tokens(epl_name))
    candidates = [p for p in pool if e_tokens & set(tokens(p))]
    if not candidates:
        s = surname(epl_name)
        if s:
            candidates = [p for p in pool if surname(p) == s]
    if not candidates:
        candidates = pool[:]
    return candidates

def map_players(epl_list, fantasy_list, threshold=70):
    """
    Returns a list of mapping dictionaries:
    {
    "epl": <epl raw>,
    "best_match": <top candidate name string or None>,
    "best_score": <score numeric or None>,
    "candidates_top3": [ {name, score, surname_match, token_overlap, fuzzy}, ... ]
    }
    Note: best_match is set to the top candidate if any (so you can always see who was top).
    """
    results = []
    for e in epl_list:
        cands = candidate_block(e, fantasy_list)
        scored = []
        for f in cands:
            s, sm, to, fz = match_score(e, f)
            scored.append((f, s, sm, to, fz))
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:5]
        best = top[0] if top else None
        results.append({
            "epl": e,
            "best_match": best[0] if best else None,
            "best_score": best[1] if best else None,
            "candidates_top3": [
                {"name": t[0], "score": t[1], "surname_match": t[2], "token_overlap": t[3], "fuzzy": t[4]}
                for t in top[:3]
            ]
        })
    return results

# -----------------------------
# Export helper (avoid duplicates by id)
# -----------------------------
def export_individual_player(player, file_path="output_files/individual_player.json", dry_run=False):
    """
    Attempts to export `player` to file_path.
    - If dry_run=True, do NOT modify the file; just return True if it would be exported (i.e. not a duplicate).
    - Duplicate detection is performed against the current contents of file_path.
    """
    players = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                players = json.load(f)
                if not isinstance(players, list):
                    players = [players]
        except json.JSONDecodeError:
            players = []

    player_id = player.get("id")
    if player_id is not None:
        if any(isinstance(p, dict) and p.get("id") == player_id for p in players):
            return False
    else:
        if player in players:
            return False

    if dry_run:
        # Would export (non-destructive simulation)
        return True

    # Real write
    players.append(player)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=4, ensure_ascii=False)
    return True

# -----------------------------
# Build normalized maps from full fantasy data
# -----------------------------
def build_normalized_maps(full_fantasy_data):
    by_display = {}
    by_name = {}
    for p in full_fantasy_data:
        d = p.get("display_name")
        n = p.get("name")
        if d:
            by_display.setdefault(normalize(d), []).append(p)
        if n:
            by_name.setdefault(normalize(n), []).append(p)
    return by_display, by_name

# -----------------------------
# Main: run stage 3 with robust export conditions and dry-run option
# -----------------------------
def run_stage3(
    epl_leftover_csv="intermediary_files/epl_players_remained_after_second_iter.csv",
    fantasy_pool_csv="intermediary_files/remaining_fantasy_display_names.csv",
    full_fantasy_json="input_files/Fantasy_LiveScoring.players.json",
    threshold=70,
    dry_run=False
):
    mode = "DRY-RUN (no changes to individual_player.json)" if dry_run else "LIVE (will write to individual_player.json)"
    print(f"Running fuzzy stage with threshold = {threshold} — {mode}")
    epl_list = load_csv(epl_leftover_csv)
    fantasy_pool = load_csv(fantasy_pool_csv)
    full_fantasy = load_json(full_fantasy_json)

    map_display, map_name = build_normalized_maps(full_fantasy)

    mapping = map_players(epl_list, fantasy_pool, threshold=threshold)

    # Print scoring info (stdout)
    for r in mapping:
        print("EPL:", r["epl"])
        print("  Best match:", r["best_match"], "Score:", r["best_score"])
        print("  Top candidates:")
        for c in r["candidates_top3"]:
            print("    -", c["name"], f"(score={c['score']}, surname_match={c['surname_match']}, token_overlap={c['token_overlap']}, fuzzy={c['fuzzy']})")
        print()
    print("rapidfuzz available:", has_rapidfuzz)
    print()

    exported_count = 0
    matched_fantasy_set = set()
    mapping_with_export_status = []

    # Iterate and export (or simulate) whenever best_score >= threshold
    for r in mapping:
        best_name = r["best_match"]
        best_score = r["best_score"] if r["best_score"] is not None else -1
        exported = False
        exported_player_id = None

        if best_name is not None and best_score >= threshold:
            # try normalized lookup in maps
            norm_best = normalize(best_name)
            candidates = map_display.get(norm_best) or map_name.get(norm_best) or []

            # If no direct map hit, do fuzzy search over full_fantasy (fallback)
            if not candidates:
                best_fallback = None
                for p in full_fantasy:
                    disp = p.get("display_name") or p.get("name") or ""
                    s, *_ = match_score(r["epl"], disp)
                    if best_fallback is None or s > best_fallback[0]:
                        best_fallback = (s, p)
                if best_fallback and best_fallback[0] >= threshold:
                    candidates = [best_fallback[1]]

            if candidates:
                chosen_player = candidates[0]  # choose first player record
                # Attempt export (or simulation)
                exported = export_individual_player(chosen_player, dry_run=dry_run)
                if exported:
                    exported_count += 1
                exported_player_id = chosen_player.get("id")
                # Only consider the fantasy name removed from pool if export (or would export) succeeded
                if exported:
                    matched_fantasy_set.add(best_name)

        mapping_with_export_status.append({
            **r,
            "exported": exported,
            "exported_player_id": exported_player_id
        })

    # write mapping details (always write this for inspection)
    write_json("intermediary_files/fuzzy_mapping_results.json", mapping_with_export_status)

    # write remaining fantasy pool after fuzzy (simulate removals in dry-run as well)
    os.makedirs("intermediary_files", exist_ok=True)
    remaining_after = [n for n in fantasy_pool if n not in matched_fantasy_set]
    with open("intermediary_files/remaining_fantasy_display_names_after_fuzzy.csv", "w", encoding="utf-8") as f:
        for n in remaining_after:
            f.write(n + "\n")

    if dry_run:
        print(f"DRY-RUN: {exported_count} player(s) would have been exported (no files modified).")
    else:
        print(f"Fuzzy stage done. Exported {exported_count} new player(s) to output_files/individual_player.json")
    print("Mapping details written to intermediary_files/fuzzy_mapping_results.json")
    print("Remaining fantasy pool after fuzzy:", len(remaining_after), "entries written to intermediary_files/remaining_fantasy_display_names_after_fuzzy.csv")

# -----------------------------
# CLI
# -----------------------------
def parse_threshold(x):
    try:
        v = float(x)
    except Exception:
        raise argparse.ArgumentTypeError("threshold must be a number between 0 and 100")
    if not (0 <= v <= 100):
        raise argparse.ArgumentTypeError("threshold must be between 0 and 100")
    return v

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 3 fuzzy matching. Exports fuzzy top matches >= threshold.")
    parser.add_argument("--threshold", "-t", type=parse_threshold, default=70,
                        help="Acceptance threshold (0-100). Defaults to 70.")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Perform a dry run: do NOT modify output_files/individual_player.json. Mapping results still written for inspection.")
    args = parser.parse_args()
    run_stage3(threshold=args.threshold, dry_run=args.dry_run)

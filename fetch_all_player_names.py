#!/usr/bin/env python3
"""
fetch_all_player_names.py

Merges the behavior of:
 - fetch_epl_player_names.py
 - fetch_fantasy_player_display_names.py
 - fetch_fantasy_player_names.py

Outputs (same as original scripts):
 - intermediary_files/epl_player_names.csv
 - intermediary_files/fantasy_player_display_names.csv
 - intermediary_files/fantasy_player_names.csv
"""

import json
import unicodedata
import os

# -------------------------
# I/O helpers
# -------------------------
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def export_csv(names, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for name in names:
            # keep same behavior as original: write only non-None names
            if name is None:
                continue
            f.write(name + "\n")

# -------------------------
# Normalization helpers (kept identical to original logic)
# -------------------------
def strip_accents(text):
    if text is None:
        return text
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )

TRANSLIT_MAP = {
    "ı": "i",  # dotless i
    "İ": "I",  # capital dotted i
    "ğ": "g",
    "Ğ": "G",
    "Ø": "O",
    "ø": "o",
}

def normalize_name_for_display(text):
    """
    Mirrors fetch_fantasy_player_display_names.py.normalize_name:
    strip accents then apply transliteration map.
    (No lowercasing here to preserve original behavior.)
    """
    if text is None:
        return None
    text = strip_accents(text)
    return "".join(TRANSLIT_MAP.get(c, c) for c in text)

# -------------------------
# Extraction functions
# -------------------------
def get_epl_player_names(epl_json_data):
    """
    Matches original fetch_epl_player_names.py behavior:
    iterate json_data[0].get("events",[]), then futures -> runners -> runnerName
    """
    names = []
    if not epl_json_data:
        return names

    # original accessed json_data[0], so we do the same
    first = epl_json_data[0]
    for event in first.get("events", []):
        # original used event.get("futures") without default; be safe and default to []
        for future in event.get("futures", []) :
            if future.get("marketType") == "PLAYER_TO_HAVE_1_OR_MORE_SHOTS":
                for runner in future.get("runners", []):
                    # original appended runner.get("runnerName")
                    names.append(runner.get("runnerName"))
    return names

def get_fantasy_player_display_names(full_fantasy_json):
    """
    Mirrors fetch_fantasy_player_display_names.py:
    - prefer display_name if present else name
    - normalize (strip accents + TRANSLIT_MAP)
    - only append when a chosen value exists (truthy)
    """
    names = []
    for player in full_fantasy_json:
        display_name = player.get("display_name")
        name = player.get("name")
        chosen = display_name if display_name else name
        if chosen:
            names.append(normalize_name_for_display(chosen))
    return names

def get_fantasy_player_names(full_fantasy_json):
    """
    Mirrors fetch_fantasy_player_names.py:
    - append raw 'name' field for every player (if present)
    """
    names = []
    for player in full_fantasy_json:
        name = player.get("name")
        # original appended name and then wrote to file; to avoid TypeError we skip None values
        if name is not None:
            names.append(name)
    return names

# -------------------------
# CLI / main
# -------------------------
if __name__ == "__main__":
    # paths used by originals
    epl_input = "input_files/epl_data.json"
    fantasy_input = "input_files/Fantasy_LiveScoring.players.json"

    epl_out = "intermediary_files/epl_player_names.csv"
    fantasy_display_out = "intermediary_files/fantasy_player_display_names.csv"
    fantasy_name_out = "intermediary_files/fantasy_player_names.csv"

    # load files
    print("Loading JSON inputs...")
    epl_json = load_json(epl_input)
    fantasy_json = load_json(fantasy_input)

    # extract
    print("Extracting EPL player names...")
    epl_names = get_epl_player_names(epl_json)
    print(f"  Found {len(epl_names)} EPL runner names; exporting to {epl_out}")

    print("Extracting fantasy display names (normalized/transliterated)...")
    fantasy_display_names = get_fantasy_player_display_names(fantasy_json)
    print(f"  Found {len(fantasy_display_names)} fantasy display names; exporting to {fantasy_display_out}")

    print("Extracting fantasy raw 'name' values...")
    fantasy_names = get_fantasy_player_names(fantasy_json)
    print(f"  Found {len(fantasy_names)} fantasy raw names; exporting to {fantasy_name_out}")

    # export CSVs
    export_csv(epl_names, epl_out)
    export_csv(fantasy_display_names, fantasy_display_out)
    export_csv(fantasy_names, fantasy_name_out)

    print("Done.")

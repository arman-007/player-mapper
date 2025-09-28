import json
import unicodedata
import os


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def export_csv(names, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for name in names:
            if name is None:
                continue
            f.write(name + "\n")

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

def get_epl_player_names(epl_json_data):
    """
    Matches original fetch_epl_player_names.py behavior:
    iterate json_data[0].get("events",[]), then futures -> runners -> runnerName
    """
    names = []
    if not epl_json_data:
        return names

    first = epl_json_data[0]
    for event in first.get("events", []):
        for future in event.get("futures", []) :
            if future.get("marketType") == "PLAYER_TO_HAVE_1_OR_MORE_SHOTS":
                for runner in future.get("runners", []):
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
        if name is not None:
            names.append(name)
    return names

if __name__ == "__main__":
    epl_input = "input_files/epl_data.json"
    fantasy_input = "input_files/Fantasy_LiveScoring.players.json"

    epl_out = "intermediary_files/epl_player_names.csv"
    fantasy_display_out = "intermediary_files/fantasy_player_display_names.csv"
    fantasy_name_out = "intermediary_files/fantasy_player_names.csv"

    print("Loading JSON inputs...")
    epl_json = load_json(epl_input)
    fantasy_json = load_json(fantasy_input)

    epl_names = get_epl_player_names(epl_json)

    fantasy_display_names = get_fantasy_player_display_names(fantasy_json)

    fantasy_names = get_fantasy_player_names(fantasy_json)

    export_csv(epl_names, epl_out)
    export_csv(fantasy_display_names, fantasy_display_out)
    export_csv(fantasy_names, fantasy_name_out)

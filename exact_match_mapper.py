import json
import os
import unicodedata
import datetime


def load_csv(file_path):
    names = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            names.append(line.strip())
    return names

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

TRANSLIT_MAP = {
    "ı": "i",  # dotless i
    "İ": "I",  # capital dotted i
    "ğ": "g",
    "Ğ": "G",
    "Ø": "O",
    "ø": "o",
}

def strip_accents(text):
    if text is None:
        return text
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )

def normalize_name(text):
    if text is None:
        return ""
    text = strip_accents(text)
    # Apply transliteration map and lower-case for robust matching:
    return "".join(TRANSLIT_MAP.get(c, c) for c in text).lower().strip()

def transliterate(text):
    if text is None:
        return None
    s = strip_accents(text)
    return "".join(TRANSLIT_MAP.get(c, c) for c in s)

def prepare_export_player(raw_player):
    # Build reduced object
    db_name = raw_player.get("display_name") or raw_player.get("name") or raw_player.get("common_name")
    fanduel_name = transliterate(db_name) if db_name else None
    player_api_id = raw_player.get("api_player_id") or raw_player.get("player_api_id")
    player_id = raw_player.get("_id")

    try:
        created_iso = datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
    except TypeError:
        created_iso = datetime.datetime.utcnow().isoformat() + "Z"

    return {
        "player_id": player_id,
        "player_api_id": player_api_id,
        "player_db_name": db_name,
        "player_fanduel_name": fanduel_name,
        "created_at": {"$date": created_iso}
    }

def export_individual_player(raw_player):
    """
    Transform raw fantasy player into reduced dict and append to output_files/mapped_players.json.
    Duplicate detection by player_api_id (preferred), else _id.$oid, else exact object.
    """
    exported = prepare_export_player(raw_player)
    file_path = "output_files/mapped_players.json"
    players = []

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                players = json.load(f)
                if not isinstance(players, list):
                    players = [players]
            except json.JSONDecodeError:
                players = []

    api_id = exported.get("player_api_id")
    db_oid = None
    pid = exported.get("player_id")
    if isinstance(pid, dict):
        db_oid = pid.get("$oid") or pid.get("oid") or None

    duplicate = False
    if api_id is not None:
        duplicate = any(isinstance(p, dict) and p.get("player_api_id") == api_id for p in players)
    elif db_oid:
        duplicate = any(isinstance(p, dict)
                        and isinstance(p.get("player_id"), dict)
                        and p.get("player_id").get("$oid") == db_oid
                        for p in players)
    else:
        duplicate = exported in players

    if duplicate:
        return False

    players.append(exported)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=4, ensure_ascii=False)
    return True

def build_normalized_map(full_fantasy_data, mapping_field):
    norm_map = {}
    for player in full_fantasy_data:
        val = player.get(mapping_field)
        if not val:
            continue
        norm = normalize_name(val)
        norm_map.setdefault(norm, []).append(player)
    return norm_map

def map_names(
        fantasy_players_csv,
        epl_players,
        full_fantasy_data,
        mapping_field,
        file_name_not_found,
        output_file_name_remaining
    ):
    fantasy_norm_list = [normalize_name(x) for x in fantasy_players_csv]
    fantasy_norm_set = set(fantasy_norm_list)

    normalized_map = build_normalized_map(full_fantasy_data, mapping_field)

    numbers_of_common_players = 0     
    numbers_of_players_not_found = 0
    not_found_players = []

    remaining_fantasy_norm = set(fantasy_norm_list)

    for epl_player in epl_players:
        norm_epl = normalize_name(epl_player)

        if norm_epl in fantasy_norm_set:
            if norm_epl in normalized_map:
                matched_players = normalized_map[norm_epl]
                exported_any = False
                for mp in matched_players:
                    exported = export_individual_player(mp)
                    if exported:
                        numbers_of_common_players += 1
                        exported_any = True
                remaining_fantasy_norm.discard(norm_epl)
                if not exported_any:
                    pass
            else:
                numbers_of_players_not_found += 1
                not_found_players.append(epl_player)
                remaining_fantasy_norm.discard(norm_epl)
        else:
            numbers_of_players_not_found += 1
            not_found_players.append(epl_player)

    print(f"Number of common players (exported records): {numbers_of_common_players}")
    print(f"Number of players not found: {numbers_of_players_not_found}")

    os.makedirs(os.path.dirname(file_name_not_found), exist_ok=True)
    with open(file_name_not_found, "w", encoding="utf-8") as f:
        for name in not_found_players:
            f.write(name + "\n")

    os.makedirs(os.path.dirname(output_file_name_remaining), exist_ok=True)
    with open(output_file_name_remaining, "w", encoding="utf-8") as f:
        for name in sorted(remaining_fantasy_norm):
            f.write(name + "\n")

if "__main__" == __name__:
    fantasy_players_display_names = load_csv("intermediary_files/fantasy_player_display_names.csv")
    epl_players = load_csv("intermediary_files/epl_player_names.csv")
    fantasy_full_data = load_json("input_files/Fantasy_LiveScoring.players.json")

    try:
        os.remove("output_files/mapped_players.json")
    except FileNotFoundError:
        pass

    map_names(
        fantasy_players_display_names,
        epl_players,
        fantasy_full_data,
        mapping_field="display_name",
        file_name_not_found="intermediary_files/epl_players_remained_after_first_iter.csv",
        output_file_name_remaining="intermediary_files/remaining_fantasy_display_names.csv"
    )

    fantasy_player_names = load_csv("intermediary_files/fantasy_player_names.csv")
    not_matched_display_names = load_csv("intermediary_files/epl_players_remained_after_first_iter.csv")

    map_names(
        fantasy_player_names, 
        not_matched_display_names, 
        fantasy_full_data,
        mapping_field="name",
        file_name_not_found="intermediary_files/epl_players_remained_after_second_iter.csv",
        output_file_name_remaining="intermediary_files/remaining_fantasy_names.csv"
    )

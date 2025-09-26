import json
import unicodedata


def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def strip_accents(text):
    # Normalize to NFKD form, then drop diacritics
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

def normalize_name(text):
    text = strip_accents(text)
    return "".join(TRANSLIT_MAP.get(c, c) for c in text)


def get_names(json_data):
    names = []
    for player in json_data:
        display_name = player.get("display_name")
        name = player.get("name")

        chosen = display_name if display_name else name
        if chosen:
            # convert to ASCII-friendly plain text
            names.append(normalize_name(chosen))

    return names


def export_csv(names):
    with open("fantasy_player_display_names.csv", "w") as f:
        for name in names:
            f.write(name + "\n")


if __name__ == "__main__":
    json_data = load_json("Fantasy_LiveScoring.players.json")
    names = get_names(json_data)
    export_csv(names)

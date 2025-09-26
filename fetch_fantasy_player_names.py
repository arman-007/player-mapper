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


def get_names(json_data):
    names = []
    for player in json_data:
        name = player.get("name")
        names.append(name)
    return names


def export_csv(names):
    with open("fantasy_player_names.csv", "w") as f:
        for name in names:
            f.write(name + "\n")


if __name__ == "__main__":
    json_data = load_json("Fantasy_LiveScoring.players.json")
    names = get_names(json_data)
    export_csv(names)

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
    counter=0
    for event in json_data[0].get("events",[]):
        for future in event.get("futures"):
            if future.get("marketType") == "PLAYER_TO_HAVE_1_OR_MORE_SHOTS":
                for runner in future.get("runners"):
                    names.append(runner.get("runnerName"))
    return names


def export_csv(names):
    with open("epl_player_names.csv", "w") as f:
        for name in names:
            f.write(name + "\n")


if __name__ == "__main__":
    json_data = load_json("epl_data.json")
    names = get_names(json_data)
    export_csv(names)

import json
import os


def load_csv(file_path):
    names = []
    with open(file_path, "r") as f:
        for line in f.readlines():
            names.append(line.strip())
    return names

def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)
    
def export_individual_player(player):
    # Define the file path
    file_path = "individual_player.json"
    
    # Initialize an empty list to store players
    players = []
    
    # Check if the file exists and read existing data
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                players = json.load(f)
                # Ensure players is a list
                if not isinstance(players, list):
                    players = [players]
            except json.JSONDecodeError:
                # If file is empty or corrupted, start with an empty list
                players = []
    
    # Append the new player to the list
    players.append(player)
    
    # Write the updated list back to the file
    with open(file_path, "w") as f:
        json.dump(players, f, indent=4)
    
def fetch_individual_fantasy_player(name, fantasy_data, mapping_field):
    for player in fantasy_data:
        if mapping_field in player:
            if player[mapping_field] == name:
                export_individual_player(player)
        else:
            pass

def map_names(
        fantasy_players, 
        epl_players, 
        full_fantasy_data,
        mapping_field,
        file_name, 
        output_file_name
    ):
    numbers_of_common_players = 0
    numbers_of_players_not_found = 0
    not_found_players = []
    for epl_player in epl_players:
        if epl_player in fantasy_players:
            numbers_of_common_players += 1
            fantasy_players.remove(epl_player)
            fetch_individual_fantasy_player(epl_player, full_fantasy_data, mapping_field)
        else:
            numbers_of_players_not_found += 1
            not_found_players.append(epl_player)
    print(f"Number of common players: {numbers_of_common_players}")
    print(f"Number of players not found: {numbers_of_players_not_found}")
    with open(f"{file_name}", "w") as f:
        for name in not_found_players:
            f.write(name + "\n")
    with open(f"{output_file_name}", "w") as f:
        for name in fantasy_players:
            f.write(name + "\n")

if "__main__" == __name__:
    fantasy_players_display_names = load_csv("fantasy_player_display_names.csv")
    epl_players = load_csv("epl_player_names.csv")

    fantasy_full_data = load_json("Fantasy_LiveScoring.players.json")

    map_names(
        fantasy_players_display_names,
        epl_players,
        fantasy_full_data,
        mapping_field="display_name",
        file_name="epl_players_remained_after_first_iter.csv",
        output_file_name="remaining_fantasy_display_names.csv"
    )

    # fantasy_player_names = load_csv("fantasy_player_names.csv")
    # not_matched_display_names = load_csv("epl_players_remained_after_first_iter.csv")

    # map_names(
    #     fantasy_player_names, 
    #     not_matched_display_names, 
    #     fantasy_full_data,
    #     mapping_field="name",
    #     file_name="epl_players_remained_after_second_iter.csv",
    #     output_file_name="remaining_fantasy_names.csv"
    # )
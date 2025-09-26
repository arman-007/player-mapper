from thefuzz import process, fuzz

# --- 1. Input Data ---
# The two lists of player names you want to map.

def load_csv(file_path):
    names = []
    with open(file_path, "r") as f:
        for line in f.readlines():
            names.append(line.strip())
    return names

# EPL_players = [
#     "Igor Julio",
#     "Hamed Traore",
#     "Eli Kroupi",
#     "Ben Gannon-Doak",
#     "Hwang Hee-Chan",
#     "Youssef Chermiti",
#     "John Doe" # Added an example of a player with no match
# ]

# fantasy_players = [
#     "Mohamed Elyounoussi",
#     "Mohamed Elneny",
#     "Eli Junior Kroupi",
#     "Ben Osborn",
#     "Ben Mee",
#     "Ben Godfrey",
#     "Benjamin Fredrick",
#     "Elijah Adebayo",
#     "Ben Doak",
#     "Ben Knight",
#     "Hamed Junior Traore",
#     "Hee-chan Hwang",
#     "Ui-Jo Hwang",
#     "Igor",
#     "Igor Jesus",
#     "Chermiti",
#     "Kadan Young",
#     "Ashley Young"
# ]

# --- 2. Configuration ---
# The confidence score threshold (out of 100).
# A match will only be considered valid if its score is above this value.
# You can adjust this value based on your data's strictness requirements.
SCORE_THRESHOLD = 85

# --- 3. The Matching Logic ---
def map_players(source_players, choice_players, threshold):
    """
    Maps players from a source list to a list of choices using fuzzy matching.

    Args:
        source_players (list): The list of names to find matches for.
        choice_players (list): The list of names to match against.
        threshold (int): The minimum score (0-100) to consider a match.

    Returns:
        tuple: A tuple containing two lists: (successful_mappings, unmatched_players)
    """
    successful_mappings = []
    unmatched_players = []
    
    # Using a set for faster removal of matched choices
    remaining_choices = set(choice_players)

    for player_name in source_players:
        # process.extractOne is an optimized function to find the single best match.
        # It takes the query name, the list of choices, and the scoring algorithm.
        # We use token_set_ratio because it handles different word order and extra words.
        best_match = process.extractOne(
            player_name, 
            remaining_choices, 
            scorer=fuzz.token_set_ratio
        )

        if best_match and best_match[1] >= threshold:
            # If a high-confidence match is found...
            matched_name = best_match[0]
            score = best_match[1]
            
            successful_mappings.append((player_name, matched_name, score))
            
            # Remove the matched name from the choices to prevent it from being matched again.
            # This handles cases where two source players might map to the same choice.
            remaining_choices.remove(matched_name)
        else:
            # If no match is found above the threshold...
            unmatched_players.append(player_name)
            
    return successful_mappings, unmatched_players

# --- 4. Execution and Reporting ---
if __name__ == "__main__":
    EPL_players = load_csv("epl_players_remained_after_second_iter.csv")
    fantasy_players = load_csv("remaining_fantasy_display_names.csv")
    mapped, unmatched = map_players(EPL_players, fantasy_players, SCORE_THRESHOLD)

    print("--- Player Mapping Report ---")
    print(f"Confidence Threshold set to: {SCORE_THRESHOLD}\n")

    print("✅ Successful Mappings:")
    if mapped:
        for original, matched_to, score in mapped:
            print(f"  - '{original}' -> '{matched_to}' (Score: {score})")
    else:
        print("  No successful mappings found.")

    print("\n❌ Unmatched Players:")
    if unmatched:
        for name in unmatched:
            print(f"  - Could not find a confident match for '{name}'")
    else:
        print("  All players were successfully matched.")
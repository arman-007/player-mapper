#!/bin/bash

echo "Starting execution of specific Python scripts..."

python fetch_epl_player_names.py

python fetch_fantasy_player_display_names.py

python fetch_fantasy_player_names.py

python final.py

# python final_fuzzy_matcher.py
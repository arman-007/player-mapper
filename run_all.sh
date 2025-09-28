#!/bin/bash

echo "Starting execution of specific Python scripts..."

python fetch_all_player_names.py

python exact_match_mapper.py

python fuzzy_matcher.py --threshold 50
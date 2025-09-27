#!/bin/bash

echo "Starting execution of specific Python scripts..."

python fetch_all_player_names.py

python final_chatgpt.py

python final_fuzzy_matcher_chatgpt.py --threshold 50
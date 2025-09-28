
# Player-mapper

A small pipeline to map EPL betting player names to fantasy player records.  
This repository extracts names from source JSONs, performs deterministic matching, and runs a fuzzy-matching stage (configurable). It produces matched player JSONs and intermediary CSVs for human inspection and debugging.

---

## Table of contents

- [Overview](#overview)  
- [Repository layout](#repository-layout)  
- [Prerequisites](#prerequisites)  
- [Quick setup (Linux / macOS)](#quick-setup-linux--macos)  
- [Run the pipeline](#run-the-pipeline)  
  - [Using `run_all.sh` (Linux / WSL / Git Bash)](#using-run_allsh-linux--wsl--git-bash)  
  - [Stage 3 options (fuzzy matcher)](#stage-3-options-fuzzy-matcher)  
- [Outputs you will get](#outputs-you-will-get)  

---

## Overview

Pipeline stages:

1. **Extraction** — `fetch_all_player_names.py` reads:
   - `input_files/epl_data.json` and extracts EPL "runner" names for the `PLAYER_TO_HAVE_1_OR_MORE_SHOTS` market.
   - `input_files/Fantasy_LiveScoring.players.json` and exports:
     - normalized/transliterated `display_name` list (`intermediary_files/fantasy_player_display_names.csv`)
     - raw `name` list (`intermediary_files/fantasy_player_names.csv`)
     - EPL runner names (`intermediary_files/epl_player_names.csv`)

2. **Deterministic mapping** — `exact_match_mapper.py` attempts exact matches between the EPL names and fantasy display/name CSVs and writes matched player objects into `output_files/individual_player.json`. It also writes "not found" CSVs for leftovers.

3. **Fuzzy matching** — `fuzzy_matcher.py` runs a token/surname/fuzzy scoring algorithm over the remaining unmatched names to increase coverage. It supports:
   - `--threshold` (default: `70`) to accept matches.
   - `--dry-run` (`-n`) to simulate exports without modifying `individual_player.json`.

---

## Repository layout

Example layout (update if your repo differs):

```
.
├── input_files/
│   ├── epl_data.json
│   └── Fantasy_LiveScoring.players.json
├── intermediary_files/
│   ├── epl_player_names.csv
│   ├── fantasy_player_display_names.csv
│   ├── fantasy_player_names.csv
│   └── fuzzy_mapping_results.json
├── output_files/
│   └── individual_player.json
├── fetch_all_player_names.py
├── exact_match_mapper.py
├── fuzzy_matcher.py
├── run_all.sh
└── README.md
```

---

## Prerequisites

- **Python 3.8+** (3.9/3.10/3.11 recommended)
- `pip` for package installation
- (Optional on Windows) WSL or Git Bash to run `run_all.sh` directly

---

## Quick setup (Linux / macOS)

```bash
# 1. Clone repo and cd into project
git clone git@github.com:arman-007/player-mapper.git
cd player-mapper

# 2. Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify rapidfuzz (optional)
python -c "import rapidfuzz; print('rapidfuzz', rapidfuzz.__version__)"
```

---

## Run the pipeline

### Using `run_all.sh` (Linux / WSL / Git Bash)

`run_all.sh` (example) runs the three stages in order:

```bash
#!/bin/bash
echo "Starting execution of specific Python scripts..."

python fetch_all_player_names.py
python exact_match_mapper.py
python fuzzy_matcher.py --threshold 50
```

Make it executable and run:

```bash
chmod +x run_all.sh
./run_all.sh
```


### Stage 3 options (fuzzy matcher)

`fuzzy_matcher.py` supports:

- `--threshold`, `-t` : float in range 0–100. Default `70`. Lowering increases matches but may add false positives.
- `--dry-run`, `-n` : simulate the export; do not modify `output_files/individual_player.json`.

Examples:

```bash
# real run, default threshold 70
python fuzzy_matcher.py

# real run, accept looser matches (threshold 60)
python fuzzy_matcher.py --threshold 60

# dry run, no writes (simulate)
python fuzzy_matcher.py --dry-run

# dry run with custom threshold
python fuzzy_matcher.py --threshold 50 --dry-run
```

---

## Outputs you will get

- `output_files/individual_player.json` — list of exported fantasy player objects (deterministic + fuzzy).
- `intermediary_files/epl_player_names.csv` — extracted EPL runner names.
- `intermediary_files/fantasy_player_display_names.csv` — normalized/transliterated fantasy display names.
- `intermediary_files/fantasy_player_names.csv` — raw fantasy `name` field list.
- `intermediary_files/epl_players_remained_after_first_iter.csv` — EPL names not matched in first pass.
- `intermediary_files/epl_players_remained_after_second_iter.csv` — leftovers after second pass (if used).
- `intermediary_files/remaining_fantasy_display_names.csv` — fantasy pool left after deterministic passes.
- `intermediary_files/fuzzy_mapping_results.json` — structured output from fuzzy stage with scores and export status.
- `intermediary_files/remaining_fantasy_display_names_after_fuzzy.csv` — remaining fantasy names after fuzzy stage.

---
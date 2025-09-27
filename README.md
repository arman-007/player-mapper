
# Player-mapper

A small pipeline to map EPL betting player names to fantasy player records.  
This repository extracts names from source JSONs, performs deterministic matching, and runs a fuzzy-matching stage (configurable). It produces matched player JSONs and intermediary CSVs for human inspection and debugging.

---

## Table of contents

- [Overview](#overview)  
- [Repository layout](#repository-layout)  
- [Prerequisites](#prerequisites)  
- [Quick setup (Linux / macOS)](#quick-setup-linux--macos)  
- [Quick setup (Windows — CMD / PowerShell / WSL / Git Bash)](#quick-setup-windows---cmd--powershell--wsl--git-bash)  
- [requirements.txt (suggested)](#requirementstxt-suggested)  
- [Run the pipeline](#run-the-pipeline)  
  - [Using `run_all.sh` (Linux / WSL / Git Bash)](#using-run_allsh-linux--wsl--git-bash)  
  - [Windows (no Bash) — run scripts manually or use `run_all.bat` sample](#windows-no-bash----run-scripts-manually-or-use-run_allbat-sample)  
  - [Stage 3 options (fuzzy matcher)](#stage-3-options-fuzzy-matcher)  
- [Outputs you will get](#outputs-you-will-get)  
- [Troubleshooting & tips](#troubleshooting--tips)  
- [Recommended next steps / improvements](#recommended-next-steps--improvements)  
- [License](#license)

---

## Overview

Pipeline stages:

1. **Extraction** — `fetch_all_player_names.py` reads:
   - `input_files/epl_data.json` and extracts EPL "runner" names for the `PLAYER_TO_HAVE_1_OR_MORE_SHOTS` market.
   - `input_files/Fantasy_LiveScoring.players.json` and exports:
     - normalized/transliterated `display_name` list (`intermediary_files/fantasy_player_display_names.csv`)
     - raw `name` list (`intermediary_files/fantasy_player_names.csv`)
     - EPL runner names (`intermediary_files/epl_player_names.csv`)

2. **Deterministic mapping** — `final.py` (or your renamed deterministic mapper `final_chatgpt.py`) attempts exact matches between the EPL names and fantasy display/name CSVs and writes matched player objects into `output_files/individual_player.json`. It also writes "not found" CSVs for leftovers.

3. **Fuzzy matching** — `stage3_fuzzy.py` (aka `final_fuzzy_matcher_chatgpt.py`) runs a token/surname/fuzzy scoring algorithm over the remaining unmatched names to increase coverage. It supports:
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
├── final.py
├── final_fuzzy_matcher.py
├── run_all.sh
└── README.md
```

---

## Prerequisites

- **Python 3.8+** (3.9/3.10/3.11 recommended)
- `pip` for package installation
- (Optional) Git for cloning
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

## Quick setup (Windows — CMD / PowerShell / WSL / Git Bash)

### Windows (CMD)
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Windows (PowerShell)
```powershell
python -m venv venv
# If you get an ExecutionPolicy error, run (Administratively) or set process-locally:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Windows (WSL or Git Bash)
If you run a Bash-like shell, follow the Linux/macOS steps above.

---

## `requirements.txt` (suggested)

Minimal `requirements.txt` content:

```
rapidfuzz>=3.0.0
```

> `rapidfuzz` is strongly recommended (fast and accurate). If it’s not installed, the fuzzy module falls back to Python's `difflib` (slower / less accurate). To pin exact versions for reproducibility:

```bash
pip freeze > requirements.txt
```

---

## Run the pipeline

### Using `run_all.sh` (Linux / WSL / Git Bash)

`run_all.sh` (example) runs the three stages in order:

```bash
#!/bin/bash
echo "Starting execution of specific Python scripts..."

python fetch_all_player_names.py
python final.py
python final_fuzzy_matcher.py --threshold 50
```

Make it executable and run:

```bash
chmod +x run_all.sh
./run_all.sh
```

> If your deterministic mapping script is `final.py` and fuzzy script is `final_fuzzy_matcher.py`, update `run_all.sh` accordingly.

### Windows (no Bash) — run scripts manually or use `run_all.bat` sample

If you cannot run Bash on Windows, run scripts one-by-one in the activated venv:

```powershell
# After activating venv
python fetch_all_player_names.py
python final.py                              # or final_chatgpt.py
python final_fuzzy_matcher.py --threshold 50        # or final_fuzzy_matcher_chatgpt.py --threshold 50
```

**Sample `run_all.bat`** (save alongside repo):

```bat
@echo off
echo Starting execution of Python scripts...
call venv\Scripts\activate.bat
python fetch_all_player_names.py
python final.py
python final_fuzzy_matcher.py --threshold 50
pause
```

### Stage 3 options (fuzzy matcher)

`final_fuzzy_matcher.py` supports:

- `--threshold`, `-t` : float in range 0–100. Default `70`. Lowering increases matches but may add false positives.
- `--dry-run`, `-n` : simulate the export; do not modify `output_files/individual_player.json`.

Examples:

```bash
# real run, default threshold 70
python final_fuzzy_matcher.py

# real run, accept looser matches (threshold 60)
python final_fuzzy_matcher.py --threshold 60

# dry run, no writes (simulate)
python final_fuzzy_matcher.py --dry-run

# dry run with custom threshold
python final_fuzzy_matcher.py --threshold 50 --dry-run
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

## Troubleshooting & tips

- **Mismatch between counts and exported records**  
  If you see counts (e.g., "Number of common players") larger than the number of export records, it usually indicates inconsistent normalization between the CSVs and the full JSON lookup. Make sure the same normalization function is used across extraction and matching stages.

- **Rapidfuzz not installed**  
  If `rapidfuzz` is unavailable, the fuzzy script will fall back to `difflib`. Install `rapidfuzz` for better accuracy and performance:
  ```bash
  pip install rapidfuzz
  ```

- **Windows path / encoding issues**  
  Always open files with `encoding="utf-8"`. If you see `UnicodeEncodeError` or similar, set your terminal to UTF-8 or run via WSL/Git Bash.

- **Duplicate prevention**  
  Export logic avoids duplicates by checking the `id` field when present. If you re-run the pipeline and want a fresh result, delete `output_files/individual_player.json` before running.

- **Inspect borderline matches**  
  For matches with score just below threshold, consider lowering threshold slightly or exporting them to a `needs_review.csv` for manual verification.

---

## Recommended next steps / improvements

- Add `matched_by` and `match_score` provenance fields to each exported player object to make auditing easy.
- Use team/club information (if available) to disambiguate common names.
- Introduce a small `aliases.json` mapping for common name variants and nicknames.
- Provide an interactive review UI (HTML or simple CLI) for borderline fuzzy matches (e.g., 50–75).
- Add unit tests for normalization and matching logic.

---


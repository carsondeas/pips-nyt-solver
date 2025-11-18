import json
from board_objects import Domino, Region, Board
from pathlib import Path
import random
from datetime import datetime

# directory that contains the puzzle JSON files
BOARDS_DIR = Path("all_boards")

# date boundaries
START_DATE = datetime(2025, 8, 18)
END_DATE   = datetime(2025, 11, 14)

def is_valid_section(sec):
    """return true only if section contains real puzzle data."""
    if sec is None:
        return False
    if not isinstance(sec.get("dominoes"), list):
        return False
    if not isinstance(sec.get("regions"), list):
        return False
    return True


def parse_date_from_filename(filename):
    """extract a date from filenames like '2025-08-18.json'."""
    try:
        base = filename.stem  # '2025-08-18'
        return datetime.strptime(base, "%Y-%m-%d")
    except ValueError:
        return None

def parse_pips_json(path, difficulty="easy"):
    """parse a json puzzle file into a board object (dominoes + regions)."""
    with open(path, "r") as f:
        data = json.load(f)

    section = data[difficulty]
    if section is None:
        raise ValueError(f"No data for difficulty {difficulty}")

    # build domino objects
    dominoes = [
        Domino(i, d[0], d[1])
        for i, d in enumerate(section["dominoes"])
    ]

    # build region objects
    regions = [
        Region(r["indices"], r["type"], r.get("target"))
        for r in section["regions"]
    ]

    # build full board object 
    return Board(dominoes, regions)


def get_random_pips_game():
    """pick a random puzzle file within the date range and load it."""
    eligible_files = []

    for file in BOARDS_DIR.glob("*.json"):
        date = parse_date_from_filename(file)
        if date and START_DATE <= date <= END_DATE:
            eligible_files.append(file)

    if not eligible_files:
        raise FileNotFoundError("No puzzle files in the specified date range.")

    chosen_file = random.choice(eligible_files)
    with open(chosen_file, "r") as f:
        data = json.load(f)

    available = [
        d for d in ["hard"]
        if d in data and is_valid_section(data[d])
    ]

    if not available:
        raise ValueError(f"No valid difficulties found in {chosen_file}")

    chosen_difficulty = random.choice(available)
    print(f"Selected:", chosen_file.name, chosen_difficulty)

    return parse_pips_json(chosen_file, chosen_difficulty)

puzzle = get_random_pips_game()
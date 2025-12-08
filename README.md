# Pips NYT Solver
AI solvers for the New York Times **Pips** domino puzzle. The project consists of two algorithms (CSP backtracking and simulated annealing), visualizers, benchmarking tools, and utilities for downloading daily puzzles.

## Features
- **CSP solver**: backtracking search with domino domain ordering, forward checking, and region-constraints pruning; returns stats (nodes, prunes, backtracks).
- **Simulated annealing**: random init, overlap/constraint energy, Metropolis acceptance, multiple restarts.
- **Visualizers**: matplotlib stepper and pygame board player.
- **Benchmarking**: run both solvers across many boards and save comparison plots.
- **Data utilities**: fetch NYT Pips JSON boards into `all_boards/`.

## Requirements
- Python 3.10+
- pip packages: `matplotlib`, `pygame`

## Clone and local setup
1. Clone the repository:
```bash
git clone https://github.com/your-username/sentiment-analysis-bert.git
```

2. Navigate to the project directory:
```bash
cd pips-nyt-solver
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Run the GUI with a solver. Example: 
```bash
python runner.py --solver csp --pygame
```

## `runner.py` CLI
`python runner.py [options]`
- `--solver {csp, anneal, all}` choose solver(s); `all` runs both
- `--file PATH` load a specific puzzle JSON; otherwise pick a random board in range
- `--difficulty {easy, medium, hard}` section to use (default `easy`)
- `--repeat N` run N times for averages (default 1)
- `--seed INT` random seed (useful for annealing reproducibility)
- `--gui` open the matplotlib step-by-step visualizer
- `--pygame` open the pygame visualizer
- `--auto` (pygame) autoplay solver steps after solving
- `--auto-delay FLOAT` (pygame) delay between autoplay steps in seconds
- `--cell-size INT` (pygame) cell size in pixels (default 100)
- `--debug` (pygame) print solver mapping for debugging

## Usage examples
- CSP on a specific medium board:  
  `python runner.py --solver csp --difficulty medium --file all_boards/2025-11-14.json`
- Annealing on a random hard board (3 trials averaged):  
  `python runner.py --solver anneal --difficulty hard --repeat 3`
- Compare both solvers back-to-back on easy:  
  `python runner.py --solver all --difficulty easy --file all_boards/2025-11-14.json`

## Visualizers
- **Pygame board/player** (grid, constraints, domino tray):  
  `python runner.py --pygame --solver csp`
- **Matplotlib stepper** (go through placements):  
  `python runner.py --gui`


## Benchmarks and plots
- Full comparison (writes PNGs to `metrics/plots/`):  
  `python -m metrics.compare_benchmarks`
- Single-solver sweeps:  
  `python -m metrics.csp_benchmark`  
  `python -m metrics.sa_benchmark`
- Cached aggregate results: `metrics/cached_results.json`

## Data (puzzle format)
Puzzle files live at `all_boards/YYYY-MM-DD.json` and contain sections `easy`, `medium`, `hard`:
```json
{
  "dominoes": [[0,0],[0,1], ...],
  "regions": [
    {"indices": [[0,0],[0,1]], "type": "sum", "target": 5},
    {"indices": [[1,0],[1,1]], "type": "notequals"}
  ]
}
```
Cells are zero-based `(row, col)`. Region types: `equals`, `notequals`, `sum`, `less`, `greater`, `empty`.

## Repo guide
- `board_objects.py`, `load_board.py` core data structures and JSON loader
- `csp.py`, `simulated_annealing.py` solvers
- `runner.py` CLI entrypoint and visualizer hooks
- `gui/` matplotlib and pygame visualizers
- `metrics/` benchmarking and plotting utilities; outputs in `metrics/plots/`
- `fetch-all-boards.sh` download helper for daily NYT puzzles

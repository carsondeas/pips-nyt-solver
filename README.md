# Pips NYT Solver
Solver for the New York Times Pips domino puzzle. Includes a CSP backtracking solver with heuristics, a simulated annealing local search, visualizers, and benchmarking scripts.

## Install and puzzle data
- Python 3.10+ recommended.
- Install runtime deps: `pip install matplotlib pygame`.
- Puzzle JSONs: a recent set lives in `all_boards/`. To refresh, run `bash fetch-all-boards.sh`. Change date in the fetch-all-boards file.

## runner.py command line args
`python runner.py [options]`
- `--solver {csp,anneal,all}`: choose solver(s); `all` runs both.
- `--file PATH`: load a specific puzzle JSON; otherwise a random board is chosen.
- `--difficulty {easy,medium,hard}`: board difficulty to use (default `easy`).
- `--repeat N`: run N times for averages (default 1).
- `--seed INT`: random seed (useful for annealing).
- `--gui`: open the matplotlib step-by-step visualizer.
- `--pygame`: open the pygame visualizer.
- `--auto`: (pygame) autoplay solver steps after solving.
- `--auto-delay FLOAT`: (pygame) delay between autoplay steps (seconds).
- `--cell-size INT`: (pygame) cell size in pixels (default 100).
- `--debug`: (pygame) print solver mapping for debugging.

## Usage examples
- Solve one puzzle with CSP:
  `python runner.py --solver csp --difficulty medium --file all_boards/2025-11-14.json`
- Simulated annealing for a random hard puzzle, 3 trials averaged:
  `python runner.py --solver anneal --difficulty hard --repeat 3`
- Compare both solvers on an easy puzzle:
  `python runner.py --solver all --difficulty easy --file all_boards/2025-11-14.json`

## Visualizers
- Pygame board/player (grid, labels, domino tray):
  `python runner.py --pygame --solver csp`
- Matplotlib stepper (go through placements):
  `python runner.py --gui`


## Benchmarks and plots
- Full comparison (writes PNGs to `metrics/plots/`):
  `python -m metrics.compare_benchmarks`
- Single-solver runs:
  `python -m metrics.csp_benchmark`
  `python -m metrics.sa_benchmark`

## How it works
- `load_board.py`: reads NYT JSON into `Board`, `Domino`, `Region`.
- `csp.py`: backtracking with domain ordering, forward checking, and region-constraint checks; reports nodes/backtracks/prunes.
- `simulated_annealing.py`: random init, overlap/constraint energy, multiple restarts.
- `runner.py`: CLI that puts solvers, averaging, and visualizers in the command line.

## Puzzle data format
`all_boards/YYYY-MM-DD.json` contains sections `easy`, `medium`, `hard`:
```json
{
  "dominoes": [[0,0],[0,1], ...],
  "regions": [
    {"indices": [[0,0],[0,1]], "type": "sum", "target": 5},
    {"indices": [[1,0],[1,1]], "type": "notequals"}
  ]
}
```
Cells use zero-based `(row, col)`. Region types: `equals`, `notequals`, `sum`, `less`, `greater`, `empty`.

## Repo map
- `board_objects.py` / `load_board.py`: core structures and loader.
- `csp.py`, `simulated_annealing.py`: solvers.
- `runner.py`: CLI entrypoint + visualizer hooks.
- `gui/`: matplotlib and pygame visualizers.
- `metrics/`: benchmarking and plotting utilities; outputs in `metrics/plots/`.
- `fetch-all-boards.sh`: downloads NYT puzzles into `all_boards/`.

from pathlib import Path
import json
from statistics import mean, median
from load_board import parse_pips_json
import time
from datetime import datetime
from csp import solve_pips as solve_pips_csp
from simulated_annealing import solve_pips as solve_pips_sa
import matplotlib.pyplot as plt
import numpy as np
import os
import multiprocessing as mp


def _solver_worker(solver_fn, puzzle, conn):
    """Runs inside a subprocess. Sends solution back via pipe."""
    try:
        sol = solver_fn(puzzle)
        conn.send(sol)
    except Exception:
        conn.send(None)
    finally:
        conn.close()


def timed_solve(solver_fn, puzzle, timeout=3):
    """
    Run solver in a separate process and terminate
    if it exceeds timeout seconds.
    """
    parent_conn, child_conn = mp.Pipe()

    p = mp.Process(target=_solver_worker, args=(solver_fn, puzzle, child_conn))

    start = time.perf_counter()
    p.start()

    # If solver finishes in time
    if parent_conn.poll(timeout):
        solution = parent_conn.recv()
        p.join()
        duration = time.perf_counter() - start
        return solution, duration

    # Timeout -> kill the process
    p.terminate()
    p.join()
    return None, timeout

def evaluate_solvers(boards_dir):

    results = {
        "backtracking": {"times": [], "dates": [], "solved": 0},
        "annealing":    {"times": [], "dates": [], "solved": 0},
    }

    failed_backtracking = []
    failed_annealing   = []

    for file in Path(boards_dir).glob("*.json"):

        try:
            with open(file, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Skipping invalid JSON file: {file.name} ({e})")
            continue

        # parse date from filename
        try:
            puzzle_date = datetime.strptime(file.stem, "%Y-%m-%d")
        except Exception:
            print(f"Skipping file with non-date name: {file.name}")
            continue

        # loop through difficulties
        for difficulty in ["easy", "medium"]:
            if difficulty not in data:
                continue

            sec = data[difficulty]
            if sec is None:
                continue
            if not isinstance(sec.get("dominoes"), list):
                continue
            if not isinstance(sec.get("regions"), list):
                continue

            print(f"running: {file.name} [{difficulty}]")

            board = parse_pips_json(file, difficulty)

            # backtracking
            sol1, t1 = timed_solve(solve_pips_csp, board)
            results["backtracking"]["times"].append(t1)
            results["backtracking"]["dates"].append(puzzle_date)

            if sol1 is not None:
                results["backtracking"]["solved"] += 1
            else:
                failed_backtracking.append((file.name, difficulty))

            # annealing
            sol2, t2 = timed_solve(solve_pips_sa, board)
            results["annealing"]["times"].append(t2)
            results["annealing"]["dates"].append(puzzle_date)

            if sol2 is not None:
                results["annealing"]["solved"] += 1
            else:
                failed_annealing.append((file.name, difficulty))

    return results, failed_backtracking, failed_annealing

# plotting + summaries

def summarize(results):
    print("\n=== Solver Comparison Summary ===")

    for solver in ["backtracking", "annealing"]:
        times = results[solver]["times"]
        solved = results[solver]["solved"]
        total = len(times)
        print(f"\nSolver: {solver}")
        print(f"  Total puzzles: {total}")
        print(f"  Solved:        {solved} ({solved/total:.1%})")
        print(f"  Avg time:      {mean(times):.4f} sec")
        print(f"  Median time:   {median(times):.4f} sec")
        print(f"  Fastest:       {min(times):.4f} sec")
        print(f"  Slowest:       {max(times):.4f} sec")


# plot
PLOT_DIR = Path("plots")
PLOT_DIR.mkdir(exist_ok=True)


def save_plot(name):
    plt.tight_layout()
    plt.savefig(PLOT_DIR / f"{name}.png", dpi=200)
    plt.close()


def plot_solve_times_by_date(results):
    for solver in ["backtracking", "annealing"]:
        times = results[solver]["times"]
        dates = results[solver]["dates"]

        plt.figure()
        plt.scatter(dates, times)
        plt.xlabel("Date")
        plt.ylabel("Solve Time (seconds)")
        plt.title(f"{solver.capitalize()} Solve Times Over Time")
        plt.xticks(rotation=45)

        save_plot(f"{solver}_times_by_date")


def plot_combined_solve_times_by_date(results):
    bt_times = results["backtracking"]["times"]
    bt_dates = results["backtracking"]["dates"]

    sa_times = results["annealing"]["times"]
    sa_dates = results["annealing"]["dates"]

    plt.figure()
    plt.scatter(bt_dates, bt_times, alpha=0.7, label="Backtracking")
    plt.scatter(sa_dates, sa_times, alpha=0.7, label="Annealing")

    plt.xlabel("Date")
    plt.ylabel("Solve Time (seconds)")
    plt.title("Backtracking vs Annealing Solve Times Over Time")
    plt.legend()
    plt.xticks(rotation=45)

    save_plot("combined_solve_times_by_date")


def plot_middle_90_percent_by_date(results):
    bt = np.array(results["backtracking"]["times"])
    sa = np.array(results["annealing"]["times"])

    bt_dates = np.array(results["backtracking"]["dates"])
    sa_dates = np.array(results["annealing"]["dates"])

    low_bt, high_bt = np.percentile(bt, [5, 95])
    low_sa, high_sa = np.percentile(sa, [5, 95])

    bt_mask = (bt >= low_bt) & (bt <= high_bt)
    sa_mask = (sa >= low_sa) & (sa <= high_sa)

    plt.figure()
    plt.scatter(bt_dates[bt_mask], bt[bt_mask], alpha=0.7, label="Backtracking")
    plt.scatter(sa_dates[sa_mask], sa[sa_mask], alpha=0.7, label="Annealing")

    plt.xlabel("Date")
    plt.ylabel("Solve Time (seconds)")
    plt.title("Middle 90% Solve Times (5th–95th Percentile)")
    plt.legend()
    plt.xticks(rotation=45)

    save_plot("middle_90_percent_by_date")

RESULTS_CACHE = Path("cached_results.json")

def save_results(results, failed_bt, failed_sa):
    data = {
        "results": results,
        "failed_backtracking": failed_bt,
        "failed_annealing": failed_sa,
    }
    with open(RESULTS_CACHE, "w") as f:
        json.dump(data, f, default=str)  # convert dates to strings
    print(f"Saved results to {RESULTS_CACHE}")


def load_results():
    if not RESULTS_CACHE.exists():
        return None
    try:
        with open(RESULTS_CACHE, "r") as f:
            data = json.load(f)

        # Convert date strings back to datetime
        for solver in ["backtracking", "annealing"]:
            data["results"][solver]["dates"] = [
                datetime.fromisoformat(d)
                for d in data["results"][solver]["dates"]
            ]

        return (
            data["results"],
            data["failed_backtracking"],
            data["failed_annealing"],
        )
    except Exception as e:
        print("Error loading cached results:", e)
        return None


# main
def main():
    cached = load_results()

    if cached is not None:
        print("Loaded cached results.")
        results, failed_bt, failed_sa = cached
    else:
        print("No cache found. Running solvers...")
        results, failed_bt, failed_sa = evaluate_solvers(Path("all_boards"))
        save_results(results, failed_bt, failed_sa)

    summarize(results)

    # plots
    plot_solve_times_by_date(results)
    plot_combined_solve_times_by_date(results)
    plot_middle_90_percent_by_date(results)

    print("Backtracking failed on:")
    for item in failed_bt:
        print("  ", item)

    print("\nAnnealing failed on:")
    for item in failed_sa:
        print("  ", item)

    print("\nPlots saved in:  plots/\n")




if __name__ == "__main__":
    mp.freeze_support()  # required on macOS / Windows
    main()

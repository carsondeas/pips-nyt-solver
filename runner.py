import argparse
import time
import statistics
import random
from pathlib import Path

from load_board import parse_pips_json, get_random_pips_game
import csp as csp_solver
import simulated_annealing as sa_solver


def run_solver_once(board, solver_name):
    start = time.perf_counter()
    if solver_name == "csp":
        result = csp_solver.solve_pips(board)
    elif solver_name == "anneal":
        result = sa_solver.solve_pips(board)
    else:
        raise ValueError(f"Unknown solver: {solver_name}")
    elapsed = time.perf_counter() - start
    return {"solver": solver_name, "solved": result is not None, "time": elapsed}


def load_board_from_args(args):
    if args.file:
        path = Path(args.file)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {args.file}")
        return parse_pips_json(path, difficulty=args.difficulty)
    return get_random_pips_game()


def main():
    p = argparse.ArgumentParser(description="Run/benchmark Pips solvers")
    p.add_argument("--solver", choices=["csp", "anneal", "all"], default="all")
    p.add_argument("--file", help="Path to a single JSON puzzle file")
    p.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="easy")
    p.add_argument("--repeat", type=int, default=1, help="How many times to run (for averages)")
    p.add_argument("--seed", type=int, default=None)

    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    board = load_board_from_args(args)

    solvers = ["csp", "anneal"] if args.solver == "all" else [args.solver]

    summary = {}

    for solver in solvers:
        times = []
        solves = 0

        for i in range(args.repeat):
            res = run_solver_once(board, solver)
            times.append(res["time"])
            if res["solved"]:
                solves += 1
            print(f"Run {i+1}/{args.repeat} - {solver}: solved={res['solved']} time={res['time']:.4f}s")

        summary[solver] = {
            "runs": args.repeat,
            "solved_count": solves,
            "time_mean": statistics.mean(times) if times else None,
            "time_min": min(times) if times else None,
            "time_max": max(times) if times else None,
        }

    print("\n=== Summary ===")
    for s, info in summary.items():
        print(f"Solver: {s}")
        print(f"  runs: {info['runs']}")
        print(f"  solved: {info['solved_count']}/{info['runs']}")
        print(f"  time mean: {info['time_mean']:.4f}s min: {info['time_min']:.4f}s max: {info['time_max']:.4f}s")


if __name__ == '__main__':
    main()

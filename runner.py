import argparse
import time
import statistics
import random
import importlib.util
from pathlib import Path

from load_board import parse_pips_json, get_random_pips_game
import csp as csp_solver
import simulated_annealing as sa_solver
from gui.board_play import run_pygame_visualizer
from metrics.csp_benchmark import CspRunner
from metrics.sa_benchmark import SaRunner
from metrics.compare_benchmarks import main as compare_benchmarks_main


def run_solver_once(board, solver_name):
    start = time.perf_counter()
    if solver_name == "csp":
        result, stats = csp_solver.solve_pips(board, return_stats=True)
    elif solver_name == "anneal":
        result, stats = sa_solver.solve_pips(board, return_stats=True)
    else:
        raise ValueError(f"Unknown solver: {solver_name}")
    elapsed = time.perf_counter() - start
    return {
        "solver": solver_name,
        "solved": result is not None,
        "time": elapsed,
        "stats": stats,
    }


def mean_numeric_stats(stats_list):
    """Compute mean of numeric fields across a list of stat dicts."""
    if not stats_list:
        return {}
    keys = set()
    for s in stats_list:
        keys.update(s.keys())
    means = {}
    for k in sorted(keys):
        vals = [s[k] for s in stats_list if isinstance(s.get(k), (int, float))]
        if vals:
            means[k] = sum(vals) / len(vals)
    return means


def load_board_from_args(args):
    if args.file:
        path = Path(args.file)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {args.file}")
        return parse_pips_json(path, difficulty=args.difficulty)
    return get_random_pips_game(difficulty=args.difficulty)


def launch_gui(board):
    """Load and run the interactive visualizer with a provided board."""
    viz_path = Path(__file__).parent / "gui" / "step-by-step visualizer.py"
    spec = importlib.util.spec_from_file_location("step_by_step_visualizer", viz_path)
    if spec is None or spec.loader is None:
        raise ImportError("Could not load visualizer module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.interactive_demo(use_random=False, board=board)


def main():
    p = argparse.ArgumentParser(description="Run/benchmark Pips solvers")
    p.add_argument("--solver", choices=["csp", "anneal", "all"], default="all")
    p.add_argument("--file", help="Path to a single JSON puzzle file")
    p.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="easy")
    p.add_argument("--repeat", type=int, default=1, help="How many times to run (for averages)")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--gui", action="store_true", help="Launch the step-by-step visualizer")
    p.add_argument("--pygame", action="store_true", help="Launch the pygame visualizer")
    p.add_argument("--auto", action="store_true", help="(pygame) Autoplay steps after solving")
    p.add_argument("--auto-delay", type=float, default=0.5, help="(pygame) Autoplay step delay in seconds")
    p.add_argument("--cell-size", type=int, default=100, help="(pygame) Cell size in pixels")
    p.add_argument("--debug", action="store_true", help="(pygame) Print solver mapping for debugging")
    p.add_argument(
        "--stats",
        choices=["csp", "anneal", "compare"],
        help="Run benchmark stats/plots instead of a single solve",
    )

    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Stats/benchmark mode
    if args.stats:
        if args.stats == "csp":
            runner = CspRunner()
            runner.run()
            runner.summarize()
            runner.plot_mean_times()
            runner.plot_success_rates()
        elif args.stats == "anneal":
            runner = SaRunner()
            runner.run()
            runner.summarize()
            runner.plot_mean_times()
            runner.plot_success_rates()
        elif args.stats == "compare":
            compare_benchmarks_main()
        return

    board = load_board_from_args(args)

    if args.gui:
        launch_gui(board)
        return

    if args.pygame:
        solver_for_gui = args.solver
        if solver_for_gui == "all":
            solver_for_gui = "csp"
            print("Solver 'all' is not supported in pygame mode; defaulting to CSP.")
        run_pygame_visualizer(
            board,
            solver=solver_for_gui,
            cell_size=args.cell_size,
            auto=args.auto,
            delay=args.auto_delay,
            debug=args.debug,
        )
        return

    solvers = ["csp", "anneal"] if args.solver == "all" else [args.solver]

    summary = {}

    for solver in solvers:
        times = []
        solves = 0
        stats_list = []

        for i in range(args.repeat):
            res = run_solver_once(board, solver)
            times.append(res["time"])
            if res["solved"]:
                solves += 1
            if res.get("stats"):
                stats_list.append(res["stats"])
            step_info = ""
            if res.get("stats") and res["stats"].get("steps") is not None:
                step_info = f" steps={int(res['stats']['steps'])}"
            print(f"Run {i+1}/{args.repeat} - {solver}: solved={res['solved']} time={res['time']:.4f}s{step_info}")

        summary[solver] = {
            "runs": args.repeat,
            "solved_count": solves,
            "time_mean": statistics.mean(times) if times else None,
            "time_min": min(times) if times else None,
            "time_max": max(times) if times else None,
            "stats_mean": mean_numeric_stats(stats_list),
        }

    print("\n=== Summary ===")
    for s, info in summary.items():
        print(f"Solver: {s}")
        print(f"  runs: {info['runs']}")
        print(f"  solved: {info['solved_count']}/{info['runs']}")
        print(f"  time mean: {info['time_mean']:.4f}s min: {info['time_min']:.4f}s max: {info['time_max']:.4f}s")
        if info.get("stats_mean"):
            print("  stats (mean):")
            for k, v in info["stats_mean"].items():
                print(f"    {k}: {v:.2f}")


if __name__ == '__main__':
    main()

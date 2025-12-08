import json
import time
from pathlib import Path
from statistics import mean

import matplotlib.pyplot as plt

import csp
from load_board import parse_pips_json

ROOT = Path(__file__).resolve().parents[1]
DAYS_OF_DATA = 3  # last N days of boards


class CspRunner:
    def __init__(self, boards_dir=None, difficulties=None, output_dir=None):
        self.boards_dir = Path(boards_dir) if boards_dir else ROOT / "all_boards"
        self.difficulties = difficulties or ["easy", "medium", "hard"]
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).resolve().parent / "plots"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # each entry: {"time": float, "steps": int}
        self.results = {d: [] for d in self.difficulties}
        self.failures = {d: [] for d in self.difficulties}

    def solve_board(self, board):
        start = time.perf_counter()
        try:
            solution, stats = csp.solve_pips(board, return_stats=True)
        except Exception:
            solution, stats = None, None
        elapsed = time.perf_counter() - start
        return solution, elapsed, stats

    def run(self):
        if not self.boards_dir.exists():
            raise FileNotFoundError(f"Boards directory not found: {self.boards_dir}")

        files = sorted(self.boards_dir.glob("*.json"))[-DAYS_OF_DATA:]
        total_tasks = len(files) * len(self.difficulties)
        done = 0
        for puzzle_file in files:
            try:
                data = json.loads(puzzle_file.read_text())
            except Exception as e:
                print(f"Skipping invalid JSON {puzzle_file.name}: {e}")
                continue

            for diff in self.difficulties:
                section = data.get(diff)
                if not isinstance(section, dict) or "dominoes" not in section or "regions" not in section:
                    continue

                try:
                    board = parse_pips_json(puzzle_file, difficulty=diff)
                except Exception as e:
                    print(f"Skipping {puzzle_file.name}:{diff} ({e})")
                    continue

                done += 1
                start_msg = f"[CSP {done}/{total_tasks}] {puzzle_file.name}:{diff} ..."
                print(start_msg, end="\r", flush=True)
                solution, elapsed, stats = self.solve_board(board)

                status = "ok" if solution is not None else "FAILED"
                steps = stats.get("steps") if stats else None
                step_txt = f" steps={steps}" if steps is not None else ""
                finish_msg = f"[CSP {done}/{total_tasks}] {puzzle_file.name}:{diff} {status} {elapsed:.2f}s{step_txt}"
                print(finish_msg.ljust(len(start_msg)), end="\n", flush=True)

                steps = stats.get("steps") if stats else None

                if solution is not None:
                    self.results[diff].append({"time": elapsed, "steps": steps})
                else:
                    # track failure
                    self.failures[diff].append(puzzle_file.name)

        print()  # newline after progress

    def mean_times(self):
        return {
            diff: mean([r["time"] for r in runs]) if runs else None
            for diff, runs in self.results.items()
        }

    def mean_steps(self):
        means = {}
        for diff, runs in self.results.items():
            step_vals = [r["steps"] for r in runs if r.get("steps") is not None]
            means[diff] = mean(step_vals) if step_vals else None
        return means

    def summarize(self):
        for diff in self.difficulties:
            times = [r["time"] for r in self.results[diff]]
            steps = [r["steps"] for r in self.results[diff] if r.get("steps") is not None]
            solved = len(self.results[diff])
            failed = len(self.failures[diff])
            print(f"{diff}: solved {solved}, failed {failed}")
            if times:
                print(f"  mean time: {mean(times):.4f}s, fastest: {min(times):.4f}s, slowest: {max(times):.4f}s")
            if steps:
                print(f"  mean steps: {mean(steps):.0f}, fastest: {min(steps):.0f}, slowest: {max(steps):.0f}")
            if self.failures[diff]:
                print(f"  failed boards: {', '.join(self.failures[diff])}")

    def plot_mean_times(self, filename="csp_mean_times.png"):
        means = self.mean_times()
        labels = []
        values = []
        for diff in self.difficulties:
            if means[diff] is not None:
                labels.append(diff)
                values.append(means[diff])
        if not values:
            print("No data to plot.")
            return

        plt.figure(figsize=(6, 4))
        plt.bar(labels, values, color=["#4caf50", "#ffb300", "#e53935"])
        plt.ylabel("Mean solve time (s)")
        plt.title("CSP mean solve time by difficulty")
        plt.tight_layout()
        out_path = self.output_dir / filename
        plt.savefig(out_path, dpi=200)
        plt.close()
        print(f"Saved mean time plot to {out_path}")

    def plot_success_rates(self, filename="csp_success_rates.png"):
        labels = []
        rates = []
        for diff in self.difficulties:
            solved = len(self.results[diff])
            total = solved + len(self.failures[diff])
            if total == 0:
                continue
            labels.append(diff)
            rates.append(100.0 * solved / total)

        if not rates:
            print("No data to plot for success rates.")
            return

        plt.figure(figsize=(6, 4))
        plt.bar(labels, rates, color=["#4caf50", "#ffb300", "#e53935"])
        plt.ylabel("Success rate (%)")
        plt.ylim(0, 100)
        plt.title("CSP success rate by difficulty")
        plt.tight_layout()
        out_path = self.output_dir / filename
        plt.savefig(out_path, dpi=200)
        plt.close()
        print(f"Saved success rate plot to {out_path}")


def main():
    runner = CspRunner()
    runner.run()
    runner.summarize()
    runner.plot_mean_times()
    runner.plot_success_rates()


if __name__ == "__main__":
    main()

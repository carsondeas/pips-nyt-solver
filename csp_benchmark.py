import json
import time
from pathlib import Path
from statistics import mean

import matplotlib.pyplot as plt

import csp
from load_board import parse_pips_json

DAYS_OF_DATA = 60  # last 2 months of daily boards


class CspRunner:
    def __init__(self, boards_dir="all_boards", difficulties=None, output_dir="plots"):
        self.boards_dir = Path(boards_dir)
        self.difficulties = difficulties or ["easy", "medium", "hard"]
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {d: [] for d in self.difficulties}
        self.failures = {d: [] for d in self.difficulties}

    def solve_board(self, board):
        start = time.perf_counter()
        try:
            solution = csp.solve_pips(board)
        except Exception:
            solution = None
        elapsed = time.perf_counter() - start
        return solution, elapsed

    def run(self):
        if not self.boards_dir.exists():
            raise FileNotFoundError(f"Boards directory not found: {self.boards_dir}")

        files = sorted(self.boards_dir.glob("*.json"))[-DAYS_OF_DATA:]  # last ~2 months of daily boards
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
                start_msg = f"[{done}/{total_tasks}] {puzzle_file.name}:{diff} ..."
                print(start_msg, end="\r", flush=True)
                solution, elapsed = self.solve_board(board)

                status = "ok" if solution is not None else "FAILED"
                finish_msg = f"[{done}/{total_tasks}] {puzzle_file.name}:{diff} {status} {elapsed:.2f}s"
                print(finish_msg.ljust(len(start_msg)), end="\n", flush=True)

                if solution is not None:
                    self.results[diff].append(elapsed)
                else:
                    self.failures[diff].append(puzzle_file.name)

        print()  # newline after progress

    def mean_times(self):
        return {diff: mean(times) if times else None for diff, times in self.results.items()}

    def summarize(self):
        for diff in self.difficulties:
            times = self.results[diff]
            solved = len(times)
            failed = len(self.failures[diff])
            print(f"{diff}: solved {solved}, failed {failed}")
            if times:
                print(f"  mean time: {mean(times):.4f}s, fastest: {min(times):.4f}s, slowest: {max(times):.4f}s")
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

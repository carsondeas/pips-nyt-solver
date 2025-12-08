from pathlib import Path

import matplotlib.pyplot as plt

from metrics.csp_benchmark import CspRunner
from metrics.sa_benchmark import SaRunner


PLOT_DIR = Path(__file__).resolve().parent / "plots"
PLOT_DIR.mkdir(parents=True, exist_ok=True)


def combined_bar(data, title, ylabel, fname):
    diffs = ["easy", "medium", "hard"]
    width = 0.35
    x = list(range(len(diffs)))
    def _safe_vals(side: str):
        vals = []
        for d in diffs:
            v = data[side].get(d)
            vals.append(float("nan") if v is None else v)
        return vals

    csp_vals = _safe_vals("csp")
    sa_vals = _safe_vals("sa")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([i - width / 2 for i in x], csp_vals, width, label="CSP", color="#4c72b0")
    ax.bar([i + width / 2 for i in x], sa_vals, width, label="Anneal", color="#dd8452")
    ax.set_xticks(x)
    ax.set_xticklabels(diffs)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    plt.tight_layout()
    plt.savefig(PLOT_DIR / fname, dpi=200)
    plt.close()
    print(f"Saved {fname} to {PLOT_DIR}/")


def main():
    csp_runner = CspRunner(output_dir=PLOT_DIR)
    sa_runner = SaRunner(output_dir=PLOT_DIR)

    csp_runner.run()
    sa_runner.run()

    # Per-solver plots (time + annealing iterations)
    csp_runner.plot_mean_times()
    sa_runner.plot_mean_times()

    mean_times = {
        "csp": csp_runner.mean_times(),
        "sa": sa_runner.mean_times(),
    }

    success = {"csp": {}, "sa": {}}
    for runner, key in [(csp_runner, "csp"), (sa_runner, "sa")]:
        for d in runner.difficulties:
            solved = len(runner.results[d])
            total = solved + len(runner.failures[d])
            success[key][d] = 100.0 * solved / total if total else 0.0

    combined_bar(mean_times, "Mean solve time by difficulty", "Seconds", "combined_mean_times.png")
    combined_bar(success, "Success rate by difficulty", "Percent", "combined_success_rates.png")


if __name__ == "__main__":
    main()

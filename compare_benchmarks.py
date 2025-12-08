import matplotlib.pyplot as plt

from csp_benchmark import csp
from sa_benchmark import anneal


def combined_bar(data, title, ylabel, fname):
    diffs = ["easy", "medium", "hard"]
    width = 0.35
    x = list(range(len(diffs)))
    csp_vals = [data["csp"].get(d) for d in diffs]
    sa_vals = [data["sa"].get(d) for d in diffs]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([i - width / 2 for i in x], csp_vals, width, label="CSP", color="#4c72b0")
    ax.bar([i + width / 2 for i in x], sa_vals, width, label="Anneal", color="#dd8452")
    ax.set_xticks(x)
    ax.set_xticklabels(diffs)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"plots/{fname}", dpi=200)
    plt.close()
    print(f"Saved {fname} to plots/")


def main():
    csp_runner = csp()
    sa_runner = anneal()

    csp_runner.run()
    sa_runner.run()

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

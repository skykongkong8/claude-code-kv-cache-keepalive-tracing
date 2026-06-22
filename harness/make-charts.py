#!/usr/bin/env python3
"""
make-charts.py — render the experiment charts from results/{usage,kpis}.csv.

Run with matplotlib available, e.g.:
    uv run --with matplotlib python harness/make-charts.py results

Produces PNGs in RESULTS_DIR:
    1-per-turn-rate.png     per-turn cache write vs read, faceted by arm  (token-usage RATE)
    2-totals.png            grouped bar of total tokens by category, per arm (TOTAL spent)
    3-cumulative-cwt.png    cumulative cost-weighted tokens over turns
    4-verdict.png           CWT (API counterfactual) vs keepalive turns (subscription cost)
    5-chr.png               cache hit ratio per arm
Also writes ascii-summary.txt so the result survives even without matplotlib.
"""
import csv, os, sys

RESULTS = sys.argv[1] if len(sys.argv) > 1 else "results"


def load_csv(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def ascii_summary(kpis, rows):
    out = ["KPI SUMMARY (per arm)", "=" * 60]
    for k in kpis:
        out.append(
            f"{k['arm']:<12} turns={k['turns_total']:>2} "
            f"(real={k['turns_real']}, keepalive={k['turns_keepalive']})  "
            f"write={int(num(k['cache_write'])):>8,d} "
            f"read={int(num(k['cache_read'])):>9,d}  "
            f"CHR={k['CHR']}  CWT={int(num(k['CWT'])):>10,d}  ECM={k['ECM']}")
    # crude per-turn write bars
    out += ["", "PER-TURN cache_write (cold-cache spikes), '#'=~5k tokens", "-" * 60]
    for r in rows:
        bars = "#" * int(num(r["cache_write"]) / 5000)
        out.append(f"{r['arm']:<12} t{r['turn']:>2} {r['kind']:<9} "
                   f"w={int(num(r['cache_write'])):>7,d} |{bars}")
    return "\n".join(out)


def main():
    kpis = load_csv(os.path.join(RESULTS, "kpis.csv"))
    rows = load_csv(os.path.join(RESULTS, "usage.csv")) \
        if os.path.exists(os.path.join(RESULTS, "usage.csv")) else []

    with open(os.path.join(RESULTS, "ascii-summary.txt"), "w") as fh:
        fh.write(ascii_summary(kpis, rows) + "\n")
    print(ascii_summary(kpis, rows))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n[make-charts] matplotlib unavailable — wrote ascii-summary.txt only.")
        return

    arms = [k["arm"] for k in kpis]
    colors = {"write": "#d6604d", "read": "#4393c3", "input": "#999999", "output": "#7fbf7b"}

    # 1) per-turn rate, faceted by arm
    fig, axes = plt.subplots(1, max(len(arms), 1), figsize=(4 * max(len(arms), 1), 4),
                             squeeze=False)
    for ax, arm in zip(axes[0], arms):
        ar = [r for r in rows if r["arm"] == arm]
        x = [int(r["turn"]) for r in ar]
        w = [num(r["cache_write"]) for r in ar]
        rd = [num(r["cache_read"]) for r in ar]
        ax.bar(x, rd, color=colors["read"], label="cache_read (0.1x)")
        ax.bar(x, w, bottom=rd, color=colors["write"], label="cache_write")
        for r in ar:
            if r["kind"] == "keepalive":
                ax.annotate("ka", (int(r["turn"]), 0), ha="center", va="top",
                            fontsize=7, color="purple")
        ax.set_title(arm); ax.set_xlabel("turn"); ax.set_ylabel("tokens")
    axes[0][0].legend(fontsize=7)
    fig.suptitle("Per-turn token usage rate (read vs write); 'ka'=keepalive turn")
    fig.tight_layout(); fig.savefig(os.path.join(RESULTS, "1-per-turn-rate.png"), dpi=110)

    # 2) totals grouped bar
    cats = ["input", "cache_write", "cache_read", "output"]
    fig, ax = plt.subplots(figsize=(1.6 * len(arms) + 3, 4.5))
    import numpy as np
    xb = np.arange(len(arms)); width = 0.2
    for i, c in enumerate(cats):
        ax.bar(xb + (i - 1.5) * width, [num(k[c]) for k in kpis], width, label=c)
    ax.set_xticks(xb); ax.set_xticklabels(arms, rotation=15)
    ax.set_ylabel("total tokens"); ax.set_title("Total tokens spent by category, per arm")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "2-totals.png"), dpi=110)

    # 3) cumulative CWT over turns
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for arm in arms:
        ar = [r for r in rows if r["arm"] == arm]
        cum, s = [], 0.0
        for r in ar:
            s += num(r["cwt"]); cum.append(s)
        ax.plot(range(1, len(cum) + 1), cum, marker="o", label=arm)
    ax.set_xlabel("turn"); ax.set_ylabel("cumulative cost-weighted tokens")
    ax.set_title("Cumulative CWT (API-billing counterfactual)"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(RESULTS, "3-cumulative-cwt.png"), dpi=110)

    # 4) verdict twin bar: CWT vs keepalive turns
    fig, ax1 = plt.subplots(figsize=(1.6 * len(arms) + 3, 4.5))
    xb = np.arange(len(arms))
    ax1.bar(xb - 0.2, [num(k["CWT"]) for k in kpis], 0.4, color="#4393c3", label="CWT (token cost)")
    ax1.set_ylabel("CWT (token cost, API)"); ax1.set_xticks(xb)
    ax1.set_xticklabels(arms, rotation=15)
    ax2 = ax1.twinx()
    ax2.bar(xb + 0.2, [num(k["turns_keepalive"]) for k in kpis], 0.4,
            color="#d6604d", label="keepalive turns")
    ax2.set_ylabel("keepalive turns (subscription cost)")
    ax1.set_title("Verdict: token cost (API) vs extra turns (subscription)")
    fig.tight_layout(); fig.savefig(os.path.join(RESULTS, "4-verdict.png"), dpi=110)

    # 5) CHR
    fig, ax = plt.subplots(figsize=(1.4 * len(arms) + 2, 4))
    ax.bar(arms, [num(k["CHR"]) for k in kpis], color="#5aae61")
    ax.set_ylim(0, 1.05); ax.set_ylabel("cache hit ratio")
    ax.set_title("Cache Hit Ratio (read / (read+write))")
    for i, k in enumerate(kpis):
        ax.text(i, num(k["CHR"]) + 0.02, k["CHR"], ha="center", fontsize=8)
    plt.xticks(rotation=15); fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "5-chr.png"), dpi=110)

    # 6) THE money shot: cache state at the first turn AFTER the idle gap
    markers = {"wlA-off": "now also add", "wlA-on": "now also add",
               "wlB-off": "add one more test", "wlB-on": "add one more test",
               "ttl-long": "now read packages"}
    labels, writes, reads, gaps = [], [], [], []
    for arm in arms:
        m = markers.get(arm, "")
        b = next((r for r in rows if r["arm"] == arm and m in r["user_snip"].lower()), None)
        if b:
            labels.append(arm); writes.append(num(b["cache_write"]))
            reads.append(num(b["cache_read"]))
            gaps.append("70min" if arm == "ttl-long" else "7min")
    if labels:
        fig, ax = plt.subplots(figsize=(1.7 * len(labels) + 2, 4.6))
        xb = np.arange(len(labels))
        ax.bar(xb - 0.2, reads, 0.4, color=colors["read"], label="cache_read (warm)")
        ax.bar(xb + 0.2, writes, 0.4, color=colors["write"], label="cache_write (cold)")
        ax.set_xticks(xb)
        ax.set_xticklabels([f"{l}\n({g} gap)" for l, g in zip(labels, gaps)], fontsize=8)
        ax.set_ylabel("tokens on first post-gap turn")
        ax.set_title("Cache state on the first turn AFTER the idle gap\n"
                     "(read-dominated = cache survived; write spike = cache went cold)")
        ax.legend(fontsize=8)
        for i, (w, r) in enumerate(zip(writes, reads)):
            ax.text(i + 0.2, w, f"{int(w):,}", ha="center", va="bottom", fontsize=7)
        fig.tight_layout(); fig.savefig(os.path.join(RESULTS, "6-gap-boundary.png"), dpi=110)

    print(f"\n[make-charts] wrote 6 PNGs to {RESULTS}/")


if __name__ == "__main__":
    main()

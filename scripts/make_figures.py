"""
Draw the two D10.3 result figures from the scored results.

  results/figures/fig_traits.(png|svg)   treatment benchmark: correct answers for body size and habitat
  results/figures/fig_trophic.(png|svg)  trophic-guild benchmark: food named, guild of the answer,
                                         guild recorded by the pipeline, with the constant "fungi" baseline

Percentages are over scorable answers to successful requests: failed requests (the dense-retrieval
server error) are left out, so e2e_dense_generative is scored on 24 of 126 trait requests and
80 of 102 trophic requests. Whiskers are 95 % Wilson intervals.

Usage: python3 scripts/make_figures.py   (needs matplotlib; run from the repository root)
"""

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "figures"

CONFIGS = [
    ("doc_extractive", "Gold document, extractive"),
    ("doc_generative", "Gold document, generative"),
    ("e2e_sparse_extractive", "End to end, sparse, extractive"),
    ("e2e_sparse_generative", "End to end, sparse, generative\n(API default, used by the pipeline)"),
    ("e2e_dense_generative", "End to end, dense, generative"),
]
ACCENT, DARK, MID = "#2a78d6", "#52514e", "#7f7e79"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * max(0.0, c - h), 100 * min(1.0, c + h)


def is_server_error(run):
    r = run.get("response") or {}
    return bool(run.get("error")) or (not r.get("collection_results") and not r.get("model")
                                      and r.get("pipeline_time") is None)


def valid_requests(runs_path, qids):
    latest = {}
    for line in open(runs_path, encoding="utf-8"):
        if line.strip():
            x = json.loads(line)
            if x["qid"] in qids:
                latest.setdefault((x["qid"], x["config"]), []).append(x)
    ok = {}
    for (q, c), xs in latest.items():
        if any(not is_server_error(x) for x in xs):
            ok[c] = ok.get(c, 0) + 1
    return ok


def style(ax, title, subtitle):
    ax.set_xlim(-2, 102)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0 %", "25 %", "50 %", "75 %", "100 %"], color=INK2, fontsize=9)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="both", length=0)
    t = ax.figure.text(0.012, 0.985, title, fontsize=12, fontweight="bold", color=INK, va="top", linespacing=1.3)
    ax.figure.text(0.012, 0.895 if ax.figure.get_figheight() > 6 else 0.88, subtitle, fontsize=8.8, color=INK2,
                   va="top", linespacing=1.4)


def point(ax, x, y, lo, hi, color, hollow=False, marker="o", label_value=True, dy=0.0):
    ax.plot([lo, hi], [y, y], color=color, linewidth=2, solid_capstyle="round", zorder=2)
    ax.scatter([x], [y], s=64, marker=marker, zorder=3, linewidths=2,
               facecolors=SURFACE if hollow else color, edgecolors=color)
    if label_value:
        ax.text(hi + 1.2, y + dy, f"{round(x)} %", va="center", ha="left", fontsize=9, color=INK)


def row_label(ax, y0, name, lines):
    """Configuration name, then its n and request lines, right-aligned left of the plot."""
    two = "\n" in name
    ax.text(-3, y0 + (0.14 if two else 0.10), name, ha="right", va="center", fontsize=9.5, color=INK)
    first = y0 - (0.30 if two else 0.18)
    for k, line in enumerate(lines):
        ax.text(-3, first - 0.17 * k, line, ha="right", va="center", fontsize=8, color=INK2)


def fig_traits():
    rows = list(csv.DictReader(open(ROOT / "results/traits_main/scored_traits.csv", encoding="utf-8")))
    qids = {r["qid"] for r in csv.DictReader(open(ROOT / "data/benchmark_traits.csv", encoding="utf-8"))}
    ok = valid_requests(ROOT / "results/traits_main/runs.jsonl", qids)
    series = [("body_size", "Body size", ACCENT, False, "o"), ("habitat", "Habitat", DARK, False, "s")]
    fig, ax = plt.subplots(figsize=(8.6, 5.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    fig.subplots_adjust(left=0.37, right=0.96, top=0.74, bottom=0.08)
    for i, (cfg, name) in enumerate(CONFIGS):
        y0 = len(CONFIGS) - 1 - i
        ns = []
        for j, (trait, lab, col, hollow, mk) in enumerate(series):
            rs = [r for r in rows if r["config"] == cfg and r["trait"] == trait and r["plazi"] != "unscored"]
            k, n = sum(r["plazi"] == "correct" for r in rs), len(rs)
            lo, hi = wilson(k, n)
            point(ax, 100 * k / n, y0 + (0.14 if j == 0 else -0.14), lo, hi, col, hollow, mk)
            ns.append(n)
        lines = [f"n = {ns[0]} body size, {ns[1]} habitat"]
        if ok.get(cfg, 0) < len(qids):
            lines.append(f"{ok.get(cfg, 0)} of {len(qids)} requests succeeded")
        row_label(ax, y0, name, lines)
    ax.set_yticks([])
    ax.set_ylim(-0.75, len(CONFIGS) - 0.4)
    style(ax, "Given the right treatment, body size is read in 83 % of cases;\nhabitat stays at 45 % or below in every configuration",
          "Treatment benchmark: correct answers per configuration, with 95 % Wilson intervals.\n"
          "Dense retrieval is scored on its successful requests only.")
    handles = [plt.Line2D([], [], marker=mk, color=col, markerfacecolor=SURFACE if h else col, linewidth=2,
                          markersize=7, label=lab) for _, lab, col, h, mk in series]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.37, 0.80), ncol=2, frameon=False, fontsize=9)
    return fig


def fig_trophic():
    rows = list(csv.DictReader(open(ROOT / "results/trophic/scored_trophic.csv", encoding="utf-8")))
    qids = {r["qid"] for r in csv.DictReader(open(ROOT / "data/benchmark_trophic.csv", encoding="utf-8"))}
    ok = valid_requests(ROOT / "results/trophic/runs.jsonl", qids)
    base = json.load(open(ROOT / "results/trophic/summary_trophic.json"))["baselines"]
    b_doc, b_e2e = 100 * base["constant 'fungi' (doc gold)"], 100 * base["constant 'fungi' (e2e gold)"]
    series = [("food", "Food named", ACCENT, False, "o"), ("answer", "Guild of the answer", DARK, False, "s"),
              ("pipeline", "Guild recorded by the pipeline", MID, True, "o")]
    fig, ax = plt.subplots(figsize=(8.6, 6.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    fig.subplots_adjust(left=0.37, right=0.96, top=0.72, bottom=0.07)
    for i, (cfg, name) in enumerate(CONFIGS):
        y0 = len(CONFIGS) - 1 - i
        rs = [r for r in rows if r["config"] == cfg]
        n = len(rs)
        bx = b_doc if cfg.startswith("doc") else b_e2e
        ax.plot([bx, bx], [y0 - 0.36, y0 + 0.36], color=INK2, linewidth=1.2, linestyle=(0, (2, 2)), zorder=1)
        for j, (key, lab, col, hollow, mk) in enumerate(series):
            if key == "pipeline" and "generative" not in cfg:
                continue
            k = (sum(int(r["food_match"]) for r in rs) if key == "food"
                 else sum(r[key] == "correct" for r in rs))
            lo, hi = wilson(k, n)
            point(ax, 100 * k / n, y0 + 0.22 - 0.22 * j, lo, hi, col, hollow, mk)
        lines = [f"n = {n}"]
        if ok.get(cfg, 0) < len(qids):
            lines.append(f"{ok.get(cfg, 0)} of {len(qids)} requests succeeded")
        row_label(ax, y0, name, lines)
    ax.set_yticks([])
    ax.set_ylim(-0.75, len(CONFIGS) - 0.4)
    style(ax, "Generative answers name the documented food in 69 % of cases given the source\nand 44 % end to end; a constant \"fungi\" answer already scores 63–75 % on guild",
          "Trophic-guild benchmark (102 diet questions), with 95 % Wilson intervals. Dashed line: the constant answer \"fungi\",\n"
          "scored against per-question gold guilds (gold document) or the taxon's gold guilds (end to end). The pipeline\n"
          "runs in generative mode only. Dense retrieval is scored on its successful requests only.")
    handles = [plt.Line2D([], [], marker=mk, color=col, markerfacecolor=SURFACE if h else col, linewidth=2,
                          markersize=7, label=lab) for _, lab, col, h, mk in series]
    handles.append(plt.Line2D([], [], color=INK2, linewidth=1.2, linestyle=(0, (2, 2)), label='Constant "fungi" answer'))
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.37, 0.80), ncol=2, frameon=False, fontsize=9)
    return fig


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, make in (("fig_traits", fig_traits), ("fig_trophic", fig_trophic)):
        fig = make()
        for ext in ("png", "svg"):
            fig.savefig(OUT / f"{name}.{ext}", facecolor=SURFACE)
        plt.close(fig)
        print("wrote", OUT / f"{name}.png")


if __name__ == "__main__":
    main()

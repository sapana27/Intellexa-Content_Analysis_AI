"""
GENERATE ALL GRAPHS — Experiments 1, 2 and 3
FILE NAME : generate_graphs.py
LOCATION  : INTELLEXA-CONTENT_ANALYSI.../experiments/generate_graphs.py

HOW TO RUN:
    pip install matplotlib numpy
    cd experiments
    python generate_graphs.py

FIGURES PRODUCED (saved in results/figures/):
    Experiment 1:  fig1_avg_response_time.png
                   fig2_query_length.png
                   fig3_success_rate.png
                   fig4_per_query_line.png
    Experiment 2:  fig5_content_loading_time.png
                   fig6_content_success_rate.png
    Experiment 3:  fig7_mmr_diversity.png
                   fig8_mmr_coverage.png
                   fig9_mmr_combined.png
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from collections import defaultdict

# ── Global style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":        "DejaVu Sans",
    "font.size":          11,
    "axes.titlesize":     13,
    "axes.titleweight":   "bold",
    "axes.labelsize":     11,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.spines.left":   True,
    "axes.spines.bottom": True,
    "axes.linewidth":     0.8,
    "xtick.major.size":   4,
    "ytick.major.size":   4,
    "figure.dpi":         150,
    "savefig.dpi":        300,
    "savefig.bbox":       "tight",
    "figure.facecolor":   "white",
    "axes.facecolor":     "#F8F9FA",
    "grid.color":         "white",
    "grid.linewidth":     1.2,
})

COLORS = {
    "web":     "#3A7DD1",
    "pdf":     "#2EAA74",
    "general": "#9B5FC0",
    "mmr":     "#D4622A",
    "std":     "#4A85C8",
    "success": "#2EAA74",
    "anomaly": "#E8A020",
    "fail":    "#CC3B2F",
}

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)


def save_fig(name):
    path = os.path.join(FIGURES_DIR, name)
    plt.tight_layout()
    plt.savefig(path, facecolor="white")
    plt.close()
    print(f"  Saved: {path}")


def style_ax(ax):
    """Apply consistent polish to any axes."""
    ax.yaxis.grid(True, color="white", linewidth=1.2, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", which="both", length=0)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")


# =============================================================================
# EXPERIMENT 1 — Response Time
# =============================================================================

def load_exp1():
    path = os.path.join(RESULTS_DIR, "exp1_results.json")
    with open(path) as f:
        data = json.load(f)
    return [r for r in data if r["success"] and r["response_time"] >= 0.5]


def fig1_avg_response_time(results):
    by_type = defaultdict(list)
    for r in results:
        by_type[r["content_type"]].append(r["response_time"])

    types  = [t for t in ["web", "pdf", "general"] if t in by_type]
    avgs   = [sum(by_type[t]) / len(by_type[t]) for t in types]
    mins   = [min(by_type[t]) for t in types]
    maxs   = [max(by_type[t]) for t in types]
    colors = [COLORS[t] for t in types]
    errors = [
        [a - mn for a, mn in zip(avgs, mins)],
        [mx - a  for a, mx in zip(avgs, maxs)],
    ]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(
        [t.upper() for t in types], avgs,
        color=colors, width=0.45,
        yerr=errors, capsize=6,
        error_kw={"elinewidth": 1.6, "ecolor": "#555"},
        zorder=3,
    )
    for bar, val in zip(bars, avgs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(maxs) * 0.05,
            f"{val:.2f}s", ha="center", va="bottom",
            fontsize=11, fontweight="bold", color="#222",
        )

    ax.axhline(y=5, color="#CC3B2F", linestyle="--",
               linewidth=1.4, label="5 s interactive threshold", zorder=4)
    ax.set_ylabel("Response Time (seconds)")
    ax.set_title(
        "Average Response Time by Content Type\n"
        "(error bars show min–max range, n=15 per type)"
    )
    ax.set_ylim(0, max(maxs) * 1.3)
    ax.legend(fontsize=10, framealpha=0.9)
    style_ax(ax)
    save_fig("fig1_avg_response_time.png")


def fig2_query_length(results):
    data    = defaultdict(lambda: defaultdict(list))
    for r in results:
        data[r["content_type"]][r["query_length"]].append(r["response_time"])

    lengths = ["short", "medium", "long"]
    types   = [t for t in ["web", "pdf", "general"] if t in data]
    x       = np.arange(len(lengths))
    width   = 0.25

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, ct in enumerate(types):
        vals   = [
            sum(data[ct][l]) / len(data[ct][l]) if data[ct][l] else 0
            for l in lengths
        ]
        offset = (i - len(types) / 2 + 0.5) * width
        bars   = ax.bar(
            x + offset, vals, width,
            label=ct.upper(), color=COLORS[ct], alpha=0.9, zorder=3,
        )
        for bar, val in zip(bars, vals):
            if val > 0.5:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.2,
                    f"{val:.1f}s", ha="center", va="bottom", fontsize=9,
                )

    ax.set_ylabel("Average Response Time (seconds)")
    ax.set_title("Response Time by Query Complexity\n(n=5 per cell)")
    ax.set_xticks(x)
    ax.set_xticklabels(["Short Queries", "Medium Queries", "Long Queries"])
    ax.set_ylim(0, 15)
    ax.legend(fontsize=10, framealpha=0.9)
    style_ax(ax)
    save_fig("fig2_query_length.png")


def fig3_success_rate(results_all):
    path = os.path.join(RESULTS_DIR, "exp1_results.json")
    with open(path) as f:
        raw = json.load(f)

    total   = len(raw)
    success = sum(1 for r in raw if r["success"] and r["response_time"] >= 0.5)
    anomaly = sum(1 for r in raw if r["success"] and r["response_time"] < 0.5)
    fail    = total - success - anomaly

    labels = [f"Valid\n({success})", f"Anomalous*\n({anomaly})"]
    sizes  = [success, anomaly]
    colors = [COLORS["success"], COLORS["anomaly"]]
    if fail > 0:
        labels.append(f"Failed\n({fail})")
        sizes.append(fail)
        colors.append(COLORS["fail"])

    fig, ax = plt.subplots(figsize=(5.5, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors,
        autopct="%1.1f%%", startangle=90,
        textprops={"fontsize": 11},
        wedgeprops={"linewidth": 1.2, "edgecolor": "white"},
        pctdistance=0.78,
    )
    for at in autotexts:
        at.set_fontweight("bold")
        at.set_fontsize(12)

    ax.set_title(
        f"Query Execution Outcomes  (n={total} total)\n"
        f"*anomalous = sub-0.5 s silent error catch",
        fontsize=11, fontweight="bold", pad=14,
    )
    save_fig("fig3_success_rate.png")


def fig4_per_query_line(results):
    query_nos = [r["query_no"] for r in results]
    times     = [r["response_time"] for r in results]
    color_pts = [COLORS.get(r["content_type"], "#999") for r in results]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(query_nos, times, color="#CCCCCC", linewidth=1,
            linestyle="--", zorder=1)
    for qno, t, c in zip(query_nos, times, color_pts):
        ax.scatter(qno, t, color=c, s=65, zorder=3, alpha=0.92,
                   edgecolors="white", linewidths=0.5)

    ax.axhline(y=5, color="#CC3B2F", linestyle="--",
               linewidth=1.2, alpha=0.8, label="5 s threshold", zorder=2)

    patches = [
        mpatches.Patch(color=COLORS[k], label=k.upper())
        for k in ["web", "pdf", "general"]
        if k in {r["content_type"] for r in results}
    ]
    ax.legend(
        handles=patches + [
            plt.Line2D([0], [0], color="#CC3B2F",
                       linestyle="--", label="5 s threshold")
        ],
        fontsize=10, loc="upper right", framealpha=0.9,
    )
    ax.set_xlabel("Query Number")
    ax.set_ylabel("Response Time (seconds)")
    ax.set_title("Per-Query Response Time — All 45 Test Cases")
    ax.set_ylim(0, max(times) * 1.2)
    style_ax(ax)
    save_fig("fig4_per_query_line.png")


# =============================================================================
# EXPERIMENT 2 — Content Loading
# =============================================================================

def load_exp2_content():
    path = os.path.join(RESULTS_DIR, "exp2_content_loading.json")
    with open(path) as f:
        return json.load(f)


def fig5_content_loading_time(data):
    by_type = defaultdict(list)
    for r in data:
        if r["success"]:
            by_type[r["content_type"]].append(r["load_time"])

    types  = sorted(by_type.keys())
    avgs   = [sum(by_type[t]) / len(by_type[t]) for t in types]
    mins   = [min(by_type[t]) for t in types]
    maxs   = [max(by_type[t]) for t in types]
    colors = [COLORS["pdf"] if "PDF" in t else COLORS["web"] for t in types]
    errors = [
        [a - mn for a, mn in zip(avgs, mins)],
        [mx - a  for a, mx in zip(avgs, maxs)],
    ]

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    bars = ax.bar(
        types, avgs, color=colors, width=0.4,
        yerr=errors, capsize=6,
        error_kw={"elinewidth": 1.6, "ecolor": "#555"},
        zorder=3,
    )
    for bar, val in zip(bars, avgs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{val:.2f}s", ha="center", va="bottom",
            fontsize=11, fontweight="bold", color="#222",
        )

    ax.set_ylabel("Average Load Time (seconds)")
    ax.set_title(
        "Content Loading Time by Source Type\n"
        "(n=10 URLs per type, error bars = min–max)"
    )
    ax.set_ylim(0, max(maxs) * 1.3)
    style_ax(ax)
    save_fig("fig5_content_loading_time.png")


def fig6_content_success_rate(data):
    by_type = defaultdict(lambda: {"total": 0, "success": 0})
    for r in data:
        ct = r["content_type"]
        by_type[ct]["total"] += 1
        if r["success"]:
            by_type[ct]["success"] += 1

    types  = sorted(by_type.keys())
    rates  = [by_type[t]["success"] / by_type[t]["total"] * 100 for t in types]
    counts = [f"{by_type[t]['success']}/{by_type[t]['total']}" for t in types]
    colors = [COLORS["pdf"] if "PDF" in t else COLORS["web"] for t in types]

    fig, ax = plt.subplots(figsize=(6.5, 4))
    y = np.arange(len(types))
    ax.barh(y, rates, color=colors, height=0.4, alpha=0.9, zorder=3)

    for i, (rate, count) in enumerate(zip(rates, counts)):
        ax.text(
            rate + 0.8, i,
            f"{rate:.0f}%  ({count})",
            va="center", fontsize=11, fontweight="bold", color="#222",
        )

    ax.set_xlim(0, 122)
    ax.set_yticks(y)
    ax.set_yticklabels(types)
    ax.set_xlabel("Success Rate (%)")
    ax.set_title(
        "Content Loading Success Rate by Source Type\n"
        "(n=10 URLs per type)"
    )
    ax.axvline(x=100, color="#AAAAAA", linestyle="--", linewidth=0.9, zorder=2)
    ax.xaxis.grid(True, color="white", linewidth=1.2, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    save_fig("fig6_content_success_rate.png")


# =============================================================================
# EXPERIMENT 3 — MMR vs Standard Retrieval
# =============================================================================

def load_exp3():
    path = os.path.join(RESULTS_DIR, "exp3_mmr_results.json")
    with open(path) as f:
        return json.load(f)


def get_content_key(r):
    return r.get("source_label", r.get("content", "Unknown"))


def make_short_labels(contents):
    short = []
    for c in contents:
        if "RAG Wikipedia" in c or ("RAG" in c and "Web" in c):
            short.append("Web\n(RAG Wiki)")
        elif "LLM" in c:
            short.append("Web\n(LLM Wiki)")
        elif "Attention" in c or "1706" in c:
            short.append("PDF\n(Attention)")
        elif "RAG Original" in c or "2005" in c:
            short.append("PDF\n(RAG Paper)")
        else:
            short.append(c[:15])
    return short


def fig7_mmr_diversity(data):
    results    = data["results"]
    by_content = defaultdict(lambda: {"mmr": [], "std": []})
    for r in results:
        key = get_content_key(r)
        by_content[key]["mmr"].append(r["mmr_diversity"])
        by_content[key]["std"].append(r["std_diversity"])

    contents     = sorted(by_content.keys())
    short_labels = make_short_labels(contents)
    mmr_avgs = [sum(by_content[c]["mmr"]) / len(by_content[c]["mmr"]) for c in contents]
    std_avgs = [sum(by_content[c]["std"]) / len(by_content[c]["std"]) for c in contents]

    x     = np.arange(len(contents))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    b1 = ax.bar(x - width/2, mmr_avgs, width,
                label="MMR (λ=0.3)", color=COLORS["mmr"], alpha=0.9, zorder=3)
    b2 = ax.bar(x + width/2, std_avgs, width,
                label="Standard Similarity", color=COLORS["std"], alpha=0.9, zorder=3)

    all_vals = mmr_avgs + std_avgs
    y_min    = min(all_vals) - 0.02
    y_max    = max(all_vals) + 0.025

    for bar, val in zip(list(b1) + list(b2), mmr_avgs + std_avgs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + (y_max - min(all_vals)) * 0.01,
            f"{val:.4f}", ha="center", va="bottom", fontsize=9,
        )

    ax.set_ylabel("Diversity Score  (0–1, higher = better)")
    ax.set_title(
        "Retrieval Diversity Score — MMR vs Standard Similarity\n"
        "(per content source, n=20 queries each)"
    )
    ax.set_xticks(x)
    ax.set_xticklabels(short_labels, fontsize=10)
    ax.set_ylim(y_min, y_max)
    ax.legend(fontsize=10, framealpha=0.9)
    style_ax(ax)
    save_fig("fig7_mmr_diversity.png")


def fig8_mmr_coverage(data):
    results    = data["results"]
    by_content = defaultdict(lambda: {"mmr": [], "std": []})
    for r in results:
        key = get_content_key(r)
        by_content[key]["mmr"].append(r["mmr_coverage"])
        by_content[key]["std"].append(r["std_coverage"])

    contents     = sorted(by_content.keys())
    short_labels = make_short_labels(contents)
    mmr_avgs = [sum(by_content[c]["mmr"]) / len(by_content[c]["mmr"]) for c in contents]
    std_avgs = [sum(by_content[c]["std"]) / len(by_content[c]["std"]) for c in contents]

    x     = np.arange(len(contents))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    b1 = ax.bar(x - width/2, mmr_avgs, width,
                label="MMR (λ=0.3)", color=COLORS["mmr"], alpha=0.9, zorder=3)
    b2 = ax.bar(x + width/2, std_avgs, width,
                label="Standard Similarity", color=COLORS["std"], alpha=0.9, zorder=3)

    all_vals = mmr_avgs + std_avgs
    y_min    = max(0, min(all_vals) - 0.05)
    y_max    = max(all_vals) + 0.07

    for bar, val in zip(list(b1) + list(b2), mmr_avgs + std_avgs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + (y_max - min(all_vals)) * 0.015,
            f"{val:.4f}", ha="center", va="bottom", fontsize=9,
        )

    ax.set_ylabel("Coverage Score  (0–1, higher = better)")
    ax.set_title(
        "Query Coverage Score — MMR vs Standard Similarity\n"
        "(per content source, n=20 queries each)"
    )
    ax.set_xticks(x)
    ax.set_xticklabels(short_labels, fontsize=10)
    ax.set_ylim(y_min, y_max)
    ax.legend(fontsize=10, framealpha=0.9)
    style_ax(ax)
    save_fig("fig8_mmr_coverage.png")


def fig9_mmr_combined(data):
    summary = data["summary"]

    metrics  = ["Diversity Score", "Redundancy Score\n(lower = better)", "Coverage Score"]
    mmr_vals = [
        summary["mmr_diversity_avg"],
        summary["mmr_redundancy_avg"],
        summary["mmr_coverage_avg"],
    ]
    std_vals = [
        summary["std_diversity_avg"],
        summary["std_redundancy_avg"],
        summary["std_coverage_avg"],
    ]

    x     = np.arange(len(metrics))
    width = 0.3

    fig, ax = plt.subplots(figsize=(9, 5.5))
    b1 = ax.bar(x - width/2, mmr_vals, width,
                label="MMR (λ=0.3)", color=COLORS["mmr"], alpha=0.9, zorder=3)
    b2 = ax.bar(x + width/2, std_vals, width,
                label="Standard Similarity", color=COLORS["std"], alpha=0.9, zorder=3)

    # ── value labels just above each bar ──────────────────────────────────────
    all_vals = mmr_vals + std_vals
    label_pad = 0.012   # small fixed gap above bar top

    for bar, val in zip(list(b1) + list(b2), mmr_vals + std_vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + label_pad,
            f"{val:.4f}", ha="center", va="bottom",
            fontsize=9, color="#333",
        )

    # ── delta annotations placed ABOVE the value labels ──────────────────────
    # Compute the top of value-label text so arrows sit clear of it.
    # Rough text height in data units ≈ 0.018 at fontsize 9 with ylim 0–1.05
    text_height = 0.022
    annotation_pad = label_pad + text_height + 0.018   # gap above text

    for i, (mv, sv) in enumerate(zip(mmr_vals, std_vals)):
        higher = max(mv, sv)
        diff   = mv - sv
        sign   = "+" if diff >= 0 else ""
        pct    = diff / sv * 100 if sv != 0 else 0
        color  = "#2EAA74" if diff >= 0 else "#CC3B2F"
        label  = f"{sign}{pct:.2f}%"

        ax.annotate(
            label,
            xy=(x[i], higher + annotation_pad),
            ha="center", va="bottom",
            fontsize=10, fontweight="bold", color=color,
        )

    ax.set_ylabel("Score (0–1)")
    ax.set_title(
        "MMR vs Standard Retrieval — All Metrics Averaged Across 4 Sources\n"
        "(80 total query pairs, Δ% = MMR relative to Standard)"
    )
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=11)
    ax.set_ylim(0, 1.12)
    ax.legend(fontsize=10, framealpha=0.9, loc="upper right")
    style_ax(ax)
    save_fig("fig9_mmr_combined.png")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("Generating all paper figures for Intellexa...\n")

    print("── Experiment 1: Response Time (fig1–fig4) ──────────")
    exp1 = load_exp1()
    fig1_avg_response_time(exp1)
    fig2_query_length(exp1)
    fig3_success_rate(exp1)
    fig4_per_query_line(exp1)

    print("\n── Experiment 2: Content Loading (fig5–fig6) ────────")
    exp2_content = load_exp2_content()
    fig5_content_loading_time(exp2_content)
    fig6_content_success_rate(exp2_content)

    print("\n── Experiment 3: MMR vs Standard (fig7–fig9) ────────")
    exp3 = load_exp3()
    fig7_mmr_diversity(exp3)
    fig8_mmr_coverage(exp3)
    fig9_mmr_combined(exp3)

    print(f"\n✓ All 9 figures saved to: experiments/results/figures/")
    print(f"\n  fig1–fig4  →  Experiment 1 (response time)")
    print(f"  fig5–fig6  →  Experiment 2 (content loading)")
    print(f"  fig7–fig9  →  Experiment 3 (MMR retrieval)")
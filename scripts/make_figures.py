"""Generate figures for the ToolPick core-suite writeup.

Monochrome / grayscale aesthetic on purpose: no color channel to hide behind,
just the numbers. Dependency-light: matplotlib + numpy only.

Run:
    .venv/bin/python scripts/make_figures.py

Writes:
    figures/three-winners.png
    figures/domain-heatmap.png
"""

from __future__ import annotations

import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

# ---------------------------------------------------------------------------
# Frozen data (core suite: 6 domains, 108 tasks, 4 Anthropic Claude 5 models,
# default temperature). Do not recompute — these are the reported numbers.
# ---------------------------------------------------------------------------

MODELS = ["Opus 5", "Sonnet 5", "Fable 5", "Haiku 4.5"]

CORRECT = [0.74, 0.84, 0.92, 0.92]
POLICY_VIOLATIONS = [0, 1, 1, 5]
WRONG_TOOL = [1, 1, 6, 0]

DOMAINS = ["calendar", "crm", "devops", "files", "payments", "support"]

DOMAIN_CORRECT = {
    "Haiku 4.5": [0.83, 1.00, 0.92, 0.88, 1.00, 0.88],
    "Fable 5": [0.92, 0.92, 0.92, 0.88, 0.88, 1.00],
    "Sonnet 5": [0.83, 0.83, 0.83, 0.83, 0.96, 0.75],
    "Opus 5": [0.58, 0.83, 0.83, 0.67, 0.79, 0.75],
}

# Cross-vendor run: five current-generation flagships from five vendors, served
# via Fireworks AI on the full 156-task suite. Reported numbers, do not recompute.
CV_MODELS = ["Kimi K3", "gpt-oss-120b", "Qwen 3.8 Max", "DeepSeek V4 Pro", "GLM 5.2"]
CV_VENDORS = ["Moonshot", "OpenAI", "Alibaba", "DeepSeek", "Zhipu"]
CV_CORRECT = [0.87, 0.85, 0.83, 0.81, 0.78]
CV_POLICY_VIOLATIONS = [0, 6, 0, 0, 1]

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figures")

# ---------------------------------------------------------------------------
# Shared grayscale styling
# ---------------------------------------------------------------------------

BLACK = "#111111"
DARK_GRAY = "#4d4d4d"
MID_GRAY = "#8c8c8c"
LIGHT_GRAY = "#c9c9c9"
BG = "#ffffff"
GRID = "#e3e3e3"

plt.rcParams.update(
    {
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "savefig.facecolor": BG,
        "font.family": "DejaVu Sans",
        "text.color": BLACK,
        "axes.edgecolor": DARK_GRAY,
        "axes.labelcolor": BLACK,
        "xtick.color": DARK_GRAY,
        "ytick.color": DARK_GRAY,
        "font.size": 13,
        "axes.titlesize": 20,
        "axes.labelsize": 13,
    }
)


def _strip_axes(ax, keep_bottom=True):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_visible(keep_bottom)
    ax.spines["bottom"].set_color(DARK_GRAY)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(length=0)


# ---------------------------------------------------------------------------
# Figure 1: three-winners.png
# ---------------------------------------------------------------------------

def make_three_winners():
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 6.4), dpi=200)

    panels = [
        ("Correct\n(higher is better)", CORRECT, "{:.0%}", 1.0, LIGHT_GRAY, BLACK),
        ("Policy violations\n(lower is better)", POLICY_VIOLATIONS, "{:.0f}", 5, LIGHT_GRAY, BLACK),
        ("Wrong-tool errors\n(lower is better)", WRONG_TOOL, "{:.0f}", 6, LIGHT_GRAY, BLACK),
    ]

    x = np.arange(len(MODELS))

    for ax, (title, values, fmt, vmax, bar_color, edge) in zip(axes, panels):
        bars = ax.bar(x, values, width=0.6, color=bar_color, edgecolor=edge, linewidth=1.1, zorder=3)

        # Highlight every model tied for best on this metric, in solid black.
        vals_arr = np.array(values, dtype=float)
        target = vals_arr.min() if ("violations" in title or "Wrong" in title) else vals_arr.max()
        best_mask = np.isclose(vals_arr, target)
        for i in np.where(best_mask)[0]:
            bars[i].set_color(BLACK)
            bars[i].set_edgecolor(BLACK)

        for i, v in enumerate(values):
            ax.text(
                i,
                v + vmax * 0.035,
                fmt.format(v),
                ha="center",
                va="bottom",
                fontsize=12.5,
                color=BLACK,
                fontweight="bold" if best_mask[i] else "normal",
            )

        ax.set_xticks(x)
        ax.set_xticklabels(MODELS, rotation=0, fontsize=10.5)
        ax.set_ylim(0, vmax * 1.22)
        ax.set_title(title, fontsize=13.5, pad=14, color=BLACK)
        ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        ax.set_yticks([])
        _strip_axes(ax)

    fig.suptitle("One eval. Different winners.", fontsize=23, fontweight="bold", y=0.985, color=BLACK)
    fig.text(
        0.5,
        0.895,
        "Same 108 tasks, same 4 models. Opus 5 is safest (0 policy violations) despite the lowest correctness.\n"
        "Haiku 4.5 tops correctness but racks up the most policy violations. Pick your metric, pick your winner.",
        ha="center",
        va="top",
        fontsize=11.5,
        color=DARK_GRAY,
    )

    fig.text(
        0.5,
        0.01,
        "Groow Labs · ToolPick core suite · 6 domains, 108 tasks · default temperature · groowlabs.com",
        ha="center",
        va="bottom",
        fontsize=9.5,
        color=MID_GRAY,
    )

    fig.tight_layout(rect=(0, 0.06, 1, 0.80))
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "three-winners.png")
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# Figure 2: domain-heatmap.png
# ---------------------------------------------------------------------------

def make_domain_heatmap():
    row_order = ["Opus 5", "Sonnet 5", "Fable 5", "Haiku 4.5"]
    matrix = np.array([DOMAIN_CORRECT[m] for m in row_order])

    fig, ax = plt.subplots(figsize=(10.5, 5.2), dpi=200)

    cmap = plt.cm.Greys
    ax.imshow(matrix, cmap=cmap, vmin=0.5, vmax=1.0, aspect="auto")

    ax.set_xticks(np.arange(len(DOMAINS)))
    ax.set_xticklabels([d.capitalize() for d in DOMAINS], fontsize=12)
    ax.set_yticks(np.arange(len(row_order)))
    ax.set_yticklabels(row_order, fontsize=12)

    ax.set_xticks(np.arange(-0.5, len(DOMAINS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_order), 1), minor=True)
    ax.grid(which="minor", color=BG, linewidth=2.5)
    ax.tick_params(which="minor", length=0)
    ax.tick_params(which="major", length=0)
    for side in ax.spines.values():
        side.set_visible(False)

    # Annotate each cell; flip text color to white on dark cells for contrast.
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i, j]
            txt_color = "#ffffff" if val > 0.8 else BLACK
            ax.text(
                j,
                i,
                f"{val:.0%}",
                ha="center",
                va="center",
                fontsize=12.5,
                color=txt_color,
                fontweight="bold",
            )

    ax.set_title(
        "Correct, by domain\ncore suite · 108 tasks · darker = better",
        fontsize=17,
        pad=16,
        color=BLACK,
    )

    fig.text(
        0.5,
        0.02,
        "Groow Labs · ToolPick core suite · groowlabs.com",
        ha="center",
        va="bottom",
        fontsize=9.5,
        color=MID_GRAY,
    )

    fig.tight_layout(rect=(0, 0.05, 1, 1))
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "domain-heatmap.png")
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def make_cross_vendor():
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 6.8), dpi=200)
    labels = [f"{m}\n({v})" for m, v in zip(CV_MODELS, CV_VENDORS)]
    x = np.arange(len(CV_MODELS))
    panels = [
        ("Correct\n(higher is better)", CV_CORRECT, "{:.0%}", 1.0, True),
        ("Policy violations\n(lower is better)", CV_POLICY_VIOLATIONS, "{:.0f}", 6, False),
    ]
    for ax, (title, values, fmt, vmax, higher_better) in zip(axes, panels):
        bars = ax.bar(x, values, width=0.62, color=LIGHT_GRAY, edgecolor=BLACK, linewidth=1.1, zorder=3)
        vals_arr = np.array(values, dtype=float)
        target = vals_arr.max() if higher_better else vals_arr.min()
        best_mask = np.isclose(vals_arr, target)
        for i in np.where(best_mask)[0]:
            bars[i].set_color(BLACK)
            bars[i].set_edgecolor(BLACK)
        for i, v in enumerate(values):
            ax.text(
                i, v + vmax * 0.035, fmt.format(v),
                ha="center", va="bottom", fontsize=12, color=BLACK,
                fontweight="bold" if best_mask[i] else "normal",
            )
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9.5)
        ax.set_ylim(0, vmax * 1.22)
        ax.set_title(title, fontsize=13.5, pad=14, color=BLACK)
        ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        ax.set_yticks([])
        _strip_axes(ax)

    fig.suptitle("Five vendors. Score is not safety.", fontsize=23, fontweight="bold", y=0.985, color=BLACK)
    fig.text(
        0.5, 0.9,
        "Current flagships from five vendors, nearly tied on correctness (0.78 to 0.87).\n"
        "gpt-oss-120b is the second-highest scorer yet the only model to violate policy at scale.",
        ha="center", va="top", fontsize=11.5, color=DARK_GRAY,
    )
    fig.text(
        0.5, 0.01,
        "Groow Labs · ToolPick · 156 tasks · served via Fireworks AI · groowlabs.com",
        ha="center", va="bottom", fontsize=9.5, color=MID_GRAY,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.82))
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "cross-vendor.png")
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def main():
    p1 = make_three_winners()
    p2 = make_domain_heatmap()
    p3 = make_cross_vendor()
    print(f"Wrote {p1}")
    print(f"Wrote {p2}")
    print(f"Wrote {p3}")


if __name__ == "__main__":
    main()

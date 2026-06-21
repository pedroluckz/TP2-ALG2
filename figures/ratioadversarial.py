import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_PATH = os.path.join(
    BASE_DIR,
    "..",
    "testresults",
    "adversarial_results.csv"
)

OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "ratio_adversarial.png"
)

df = pd.read_csv(CSV_PATH)
df = df.sort_values("m")

df["teorico"] = np.log(df["m"]) + 1

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.labelcolor": "#222222",
    "xtick.color": "#222222",
    "ytick.color": "#222222",
    "text.color": "#111111",
    "grid.color": "#cccccc",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
    "font.size": 11,
})

RATIO_COLOR = "#1f77b4"
THEORY_COLOR = "#d62728"
N_COLOR = "#777777"

fig, ax1 = plt.subplots(
    figsize=(6, 6),
    constrained_layout=True
)

ax1.plot(
    df["m"],
    df["approx_ratio"],
    color=RATIO_COLOR,
    marker="o",
    linewidth=2,
    markersize=7,
    label="Razão de aproximação (guloso / ótimo)",
    zorder=4
)

ax1.plot(
    df["m"],
    df["teorico"],
    color=THEORY_COLOR,
    linewidth=2,
    linestyle="--",
    label=r"$\ln |X| + 1$",
    zorder=3
)

ax1.axhline(
    1,
    color="#555555",
    linewidth=1,
    linestyle=":",
    zorder=2
)

ax1.set_xlabel(
    r"$m$ (nº de elementos do universo)",
    fontsize=12
)

ax1.set_ylabel(
    "Custo guloso / Custo ótimo",
    fontsize=12
)

ax1.set_title(
    r"Razão de aproximação vs. $m$"
    "\nInstâncias Adversariais",
    fontsize=13,
    fontweight="bold",
    pad=10
)

ax1.grid(True)

ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

ax2 = ax1.twiny()

ax2.set_xlim(ax1.get_xlim())

ax2.set_xticks(df["m"].values)
ax2.set_xticklabels(
    df["n"].values,
    fontsize=8,
    color=N_COLOR,
    rotation=45
)

ax2.set_xlabel(
    r"$n$ (nº de conjuntos)",
    fontsize=11,
    color=N_COLOR
)

ax2.tick_params(
    axis="x",
    colors=N_COLOR
)

ax2.spines["top"].set_visible(True)
ax2.spines["top"].set_color("#cccccc")

ax1.legend(
    fontsize=9,
    loc="upper left",
    framealpha=0.9
)

ylo, yhi = ax1.get_ylim()

ax1.set_ylim(
    bottom=min(ylo, 0.95),
    top=max(yhi, max(df["teorico"]) * 1.05)
)

fig.savefig(
    OUTPUT_PATH,
    dpi=160,
    bbox_inches="tight"
)

plt.close(fig)

print(f"Gráfico salvo em: {OUTPUT_PATH}")
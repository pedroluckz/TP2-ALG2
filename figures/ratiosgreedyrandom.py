import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ── paths ──────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "..",
    "testresults"
)

# ── helpers ────────────────────────────────────────────────────────────────────

def parse_br_float(s):
    """Parse Brazilian-formatted floats where dots are thousands separators."""
    s = str(s).strip()
    parts = s.split('.')
    return float(''.join(parts[:-1]) + '.' + parts[-1]) if len(parts) > 2 else float(s)

# ── load data ──────────────────────────────────────────────────────────────────

greedy = pd.read_csv(
    os.path.join(RESULTS_DIR, "results_1_greedy.csv")
)

bb_files = [
    ("results_2_dfs_packingLB.csv", False),
    ("results_3_dfs_sumdegreeLB.csv", True),
    ("results_4_bestfirst_packingLB.csv", False),
    ("results_5_bestfirst_sumdegreeLB.csv", True),
]

bb_dfs = []

for fname, is_ms in bb_files:

    df = pd.read_csv(
        os.path.join(RESULTS_DIR, fname)
    )

    if is_ms:
        df["tempo_s"] = (
            df["tempo_s"]
            .apply(parse_br_float) / 1000
        )

    bb_dfs.append(
        df[df["status"] == "OPTIMAL"][["arquivo", "custo"]]
    )

# Para cada instância, usa o menor custo ótimo encontrado
optimal = (
    pd.concat(bb_dfs)
      .groupby("arquivo")["custo"]
      .min()
      .reset_index()
)

optimal.columns = ["arquivo", "custo_otimo"]

merged = greedy.merge(
    optimal,
    on="arquivo"
)

merged["ratio"] = (
    merged["custo"] /
    merged["custo_otimo"]
)

merged["teorico"] = (
    np.log(merged["m"]) + 1
)

# ── style ──────────────────────────────────────────────────────────────────────

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

# ── plot function ──────────────────────────────────────────────────────────────

def draw_ratio_plot(ax, df, x_col, xlabel, title):

    grp = (
        df.groupby(x_col)["ratio"]
          .agg(
              mean="mean",
              std="std"
          )
          .reset_index()
          .sort_values(x_col)
    )

    x = grp[x_col].values
    mean = grp["mean"].values
    std = grp["std"].fillna(0).values

    ax.fill_between(
        x,
        mean - std,
        mean + std,
        alpha=0.18,
        color=RATIO_COLOR,
        label="Média ± desvio padrão"
    )

    ax.plot(
        x,
        mean,
        color=RATIO_COLOR,
        marker="o",
        linewidth=2,
        markersize=7,
        label="Razão média (guloso / ótimo)",
        zorder=4
    )

    th = (
        df.groupby(x_col)["teorico"]
          .first()
          .reindex(grp[x_col])
          .values
    )

    ax.plot(
        x,
        th,
        color=THEORY_COLOR,
        linewidth=2,
        linestyle="--",
        label=r"$\ln|X|+1$",
        zorder=3
    )

    ax.axhline(
        1,
        color="#555555",
        linewidth=1,
        linestyle=":",
        zorder=2
    )

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel("Custo guloso / Custo ótimo", fontsize=12)
    ax.set_title(
        title,
        fontsize=13,
        fontweight="bold",
        pad=10
    )

    ax.grid(True)

    ax.legend(
        fontsize=9,
        loc="upper right",
        framealpha=0.9
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ylo, yhi = ax.get_ylim()

    ax.set_ylim(
        bottom=min(ylo, 0.95),
        top=max(yhi, max(th) * 1.05)
    )

# ── generate plots ─────────────────────────────────────────────────────────────

# 1) densidade

sub = merged[
    (merged["m"] == 75) &
    (merged["n"] == 75)
]

fig, ax = plt.subplots(
    figsize=(8, 5.5),
    constrained_layout=True
)

draw_ratio_plot(
    ax,
    sub,
    "densidade",
    "Densidade",
    r"Razão guloso/ótimo vs. Densidade ($m=75,\ n=75$)"
)

ax.set_xticks([0.1, 0.3, 0.5])

fig.savefig(
    os.path.join(BASE_DIR, "ratio_densidade.png"),
    dpi=160,
    bbox_inches="tight"
)

plt.close(fig)

# 2) n variando

sub = merged[
    (merged["m"] == 75) &
    (merged["densidade"] == 0.1)
]

fig, ax = plt.subplots(
    figsize=(8, 5.5),
    constrained_layout=True
)

draw_ratio_plot(
    ax,
    sub,
    "n",
    r"$n$ (nº de conjuntos)",
    r"Razão guloso/ótimo vs. $n$ ($m=75$, densidade$=0.1$)"
)

fig.savefig(
    os.path.join(BASE_DIR, "ratio_n_dens01.png"),
    dpi=160,
    bbox_inches="tight"
)

plt.close(fig)

# 3) m variando

sub = merged[
    (merged["n"] == 75) &
    (merged["densidade"] == 0.1)
]

fig, ax = plt.subplots(
    figsize=(8, 5.5),
    constrained_layout=True
)

draw_ratio_plot(
    ax,
    sub,
    "m",
    r"$m$ (nº de elementos)",
    r"Razão guloso/ótimo vs. $m$ ($n=75$, densidade$=0.1$)"
)

fig.savefig(
    os.path.join(BASE_DIR, "ratio_m_dens01.png"),
    dpi=160,
    bbox_inches="tight"
)

plt.close(fig)

print("Gráficos salvos com sucesso.")
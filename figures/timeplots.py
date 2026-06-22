import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "..",
    "testresults"
)

TIMEOUT_VAL = 1800

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def parse_br_float(s):
    s = str(s).strip()
    parts = s.split('.')

    if len(parts) > 2:
        return float(''.join(parts[:-1]) + '.' + parts[-1])

    return float(s)

# ──────────────────────────────────────────────────────────────
# Load CSVs
# ──────────────────────────────────────────────────────────────

files = {
    'Greedy':                    'results_1_greedy.csv',
    'DFS + Packing LB':          'results_2_dfs_packingLB.csv',
    'DFS + SumDegree LB':        'results_3_dfs_sumdegreeLB.csv',
    'Best-First + Packing LB':   'results_4_bestfirst_packingLB.csv',
    'Best-First + SumDegree LB': 'results_5_bestfirst_sumdegreeLB.csv',
}

ms_files = {
    'DFS + SumDegree LB',
    'Best-First + SumDegree LB'
}

dfs = {}

for label, fname in files.items():

    df = pd.read_csv(
        os.path.join(RESULTS_DIR, fname)
    )

    if label in ms_files:
        df['tempo_s'] = (
            df['tempo_s']
            .apply(parse_br_float) / 1000
        )
    else:
        df['tempo_s'] = pd.to_numeric(
            df['tempo_s'],
            errors='coerce'
        )

    if 'status' not in df.columns:
        df['status'] = 'OPTIMAL'

    dfs[label] = df

# ──────────────────────────────────────────────────────────────
# Visual style
# ──────────────────────────────────────────────────────────────

colors = {
    'Greedy':                    '#1f77b4',
    'DFS + Packing LB':          '#d62728',
    'DFS + SumDegree LB':        '#ff7f0e',
    'Best-First + Packing LB':   '#2ca02c',
    'Best-First + SumDegree LB': '#9467bd',
}

markers = {
    'Greedy':                    'o',
    'DFS + Packing LB':          's',
    'DFS + SumDegree LB':        '^',
    'Best-First + Packing LB':   'D',
    'Best-First + SumDegree LB': 'P',
}

plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.edgecolor': '#333333',
    'axes.labelcolor': '#222222',
    'xtick.color': '#222222',
    'ytick.color': '#222222',
    'text.color': '#111111',
    'grid.color': '#cccccc',
    'grid.linestyle': '--',
    'grid.alpha': 0.7,
    'font.size': 11,
})

# ──────────────────────────────────────────────────────────────
# Aggregation
# ──────────────────────────────────────────────────────────────

def compute_medians(groupby_col, fixed_filters, density=None):

    result = {}

    for label, df in dfs.items():

        sub = df.copy()

        for col, val in fixed_filters.items():
            sub = sub[sub[col] == val]

        if density is not None:
            sub = sub[sub['densidade'] == density]

        def agg_group(g):

            return pd.Series({
                'tempo_med': g['tempo_s'].median(),
                'is_timeout': (
                    (g['status'] == 'TIMEOUT').mean() >= 0.5
                )
            })

        grp = (
            sub.groupby(groupby_col)
               .apply(agg_group)
               .reset_index()
               .sort_values(groupby_col)
        )

        result[label] = grp

    return result

# ──────────────────────────────────────────────────────────────
# Plot
# ──────────────────────────────────────────────────────────────

def draw_plot(
    medians,
    groupby_col,
    xlabel,
    title,
    output_name,
    legend_loc='upper left'
):

    fig, ax = plt.subplots(
        figsize=(8, 5.5),
        constrained_layout=True
    )

    any_timeout = False

    for label, grp in medians.items():

        x = grp[groupby_col].values
        y = grp['tempo_med'].values

        ax.plot(
            x,
            y,
            color=colors[label],
            marker=markers[label],
            linewidth=2,
            markersize=7,
            label=label
        )

        timeout_mask = grp['is_timeout'].values

        if timeout_mask.any():

            any_timeout = True

            ax.scatter(
                x[timeout_mask],
                y[timeout_mask],
                marker='*',
                s=260,
                color=colors[label],
                edgecolors='black',
                linewidths=0.7,
                zorder=5
            )

    ax.axhline(
        TIMEOUT_VAL,
        color='#888888',
        linewidth=1.2,
        linestyle=':'
    )

    ax.set_yscale('log')

    ax.figure.canvas.draw()

    ticks = [t for t in ax.get_yticks() if t > 0]
    ticks = sorted(set(ticks + [TIMEOUT_VAL]))

    ax.set_yticks(ticks)

    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(
            lambda v, _:
            f'{int(v)}'
            if v == TIMEOUT_VAL
            else (f'{v:g}' if v >= 0.01 else f'{v:.4f}')
        )
    )

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel('Tempo mediano (s)', fontsize=12)
    ax.set_title(title, fontsize=13, fontweight='bold')

    ax.grid(True)

    handles, labels = ax.get_legend_handles_labels()

    if any_timeout:
        handles.append(
            mpatches.Patch(
                facecolor='none',
                label='★ mediana = timeout'
            )
        )
        labels.append('★ mediana = timeout')

    ax.legend(
        handles,
        labels,
        fontsize=8.5,
        loc=legend_loc,
        framealpha=0.9
    )

    output_path = os.path.join(
        BASE_DIR,
        output_name
    )

    fig.savefig(
        output_path,
        dpi=160,
        bbox_inches='tight'
    )

    plt.close(fig)

    print(f"Salvo: {output_path}")

# ──────────────────────────────────────────────────────────────
# 1) Densidade
# ──────────────────────────────────────────────────────────────

draw_plot(
    compute_medians(
        'densidade',
        {'m': 75, 'n': 75}
    ),
    'densidade',
    'Densidade',
    'Tempo mediano vs. Densidade (m=75, n=75)',
    'tempo_densidade.png',
    legend_loc='upper right'
)

# ──────────────────────────────────────────────────────────────
# 2) n variando (m=75, densidade=0.1)
# ──────────────────────────────────────────────────────────────

draw_plot(
    compute_medians(
        'n',
        {'m': 75},
        density=0.1
    ),
    'n',
    'n (nº de conjuntos)',
    'Tempo mediano vs. n (m=75, densidade=0.1)',
    'tempo_n_dens01.png'
)

# ──────────────────────────────────────────────────────────────
# 3) m variando (n=75, densidade=0.1)
# ──────────────────────────────────────────────────────────────

draw_plot(
    compute_medians(
        'm',
        {'n': 75},
        density=0.1
    ),
    'm',
    'm (nº de elementos)',
    'Tempo mediano vs. m (n=75, densidade=0.1)',
    'tempo_m_dens01.png'
)

print("Gráficos gerados com sucesso.")
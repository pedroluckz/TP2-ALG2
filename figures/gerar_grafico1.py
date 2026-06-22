import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "testresults")
OUTPUT_PATH = os.path.join(BASE_DIR, "memoria_media_comparativo.png")

CONFIGURACOES = {
    "DFS + Packing": {
        "arquivo": "results_2_dfs_packingLB.csv",
        "cor": "#2ca02c",
        "marcador": "o"
    },
    "DFS + SumDegree": {
        "arquivo": "results_3_dfs_sumdegreeLB.csv",
        "cor": "#bcbd22",
        "marcador": "^"
    },
    "Best-First + Packing": {
        "arquivo": "results_4_bestfirst_packingLB.csv",
        "cor": "#d62728",
        "marcador": "s"
    },
    "Best-First + SumDegree": {
        "arquivo": "results_5_bestfirst_sumdegreeLB.csv",
        "cor": "#ff7f0e",
        "marcador": "D"
    }
}

EIXO_X = "n"

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

fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)

for label, config in CONFIGURACOES.items():
    caminho_completo = os.path.join(RESULTS_DIR, config["arquivo"])

    if os.path.exists(caminho_completo):
        df = pd.read_csv(caminho_completo)
        
        df_agrupado = df.groupby(EIXO_X, as_index=False)["memoria_mb"].mean()
        df_agrupado = df_agrupado.sort_values(EIXO_X)
        
        ax.plot(
            df_agrupado[EIXO_X],
            df_agrupado["memoria_mb"],
            color=config["cor"],
            marker=config["marcador"],
            linewidth=2,
            markersize=6,
            label=label,
            zorder=3
        )
    else:
        print(f"Aviso: Arquivo não encontrado em {caminho_completo}")

ax.set_yscale("log")
ax.set_xlabel("Número de conjuntos (n)" if EIXO_X == "n" else "Densidade", fontsize=12)
ax.set_ylabel("Média de Memória Consumida (MB)", fontsize=12)
ax.set_title("Comparativo de Média de Memória", fontsize=13, fontweight="bold", pad=10)
ax.grid(True, which="both", ls="--", alpha=0.5)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(fontsize=10, loc="best", framealpha=0.9)

fig.savefig(OUTPUT_PATH, dpi=160, bbox_inches="tight")
print(f"Gráfico salvo com sucesso em: {OUTPUT_PATH}")
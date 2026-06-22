import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "testresults")
OUTPUT_PATH = os.path.join(BASE_DIR, "arvore_busca_comparativo.png")

CONFIGURACOES = {
    "PackingLB": {
        "arquivo": "results_2_dfs_packingLB.csv", 
        "cor": "#1f77b4", 
        "marcador": "o"
    },
    "SumDegreeLB": {
        "arquivo": "results_3_dfs_sumdegreeLB.csv", 
        "cor": "#ff7f0e", 
        "marcador": "s"
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
        
        df_agrupado = df.groupby(EIXO_X, as_index=False)["nos_explorados"].mean()
        df_agrupado = df_agrupado.sort_values(EIXO_X)
        
        ax.plot(
            df_agrupado[EIXO_X],
            df_agrupado["nos_explorados"],
            color=config["cor"],
            marker=config["marcador"],
            linewidth=2,
            markersize=7,
            label=label,
            zorder=3
        )
    else:
        print(f"Aviso: Arquivo não encontrado em {caminho_completo}")

ax.set_yscale("log")
ax.set_xlabel("Dificuldade da Instância (Número de conjuntos $n$)", fontsize=12)
ax.set_ylabel("Média de Nós Explorados (Escala Log)", fontsize=12)
ax.set_title("Tamanho da Árvore de Busca\nPackingLB vs SumDegreeLB", fontsize=13, fontweight="bold", pad=10)
ax.grid(True, which="both", linestyle="--", alpha=0.6)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(fontsize=11, loc="upper left", framealpha=0.9)

fig.savefig(OUTPUT_PATH, dpi=160, bbox_inches="tight")
print(f"Gráfico salvo em: {OUTPUT_PATH}")
plt.show()
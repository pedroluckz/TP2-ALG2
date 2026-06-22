import pandas as pd
import glob
import matplotlib.pyplot as plt
import os

# --- CÓDIGO SEGURO PARA CAMINHOS ---
# Descobre a pasta real onde este script está salvo (pasta 'figures')
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()

# Sobe um nível e entra na pasta 'or_results' de forma absoluta
csv_dir = os.path.abspath(os.path.join(script_dir, '..', 'OR_results'))
# ------------------------------------

def main():
    # 1. Carregar os resultados do algoritmo Greedy
    greedy_file = os.path.join(csv_dir, 'or_results_1_greedy.csv')
    try:
        greedy_df = pd.read_csv(greedy_file)
    except FileNotFoundError:
        print(f"Erro: Não foi possível encontrar o ficheiro em: {greedy_file}")
        return
    
    # 2. Carregar e concatenar os resultados do algoritmo DFS + SumDegreeLB
    dfs_pattern = os.path.join(csv_dir, 'or_results_2*_dfs_sumdegreeLB_*.csv')
    dfs_files = glob.glob(dfs_pattern)
    
    if not dfs_files:
        print(f"Erro: Nenhum ficheiro DFS encontrado em: {dfs_pattern}")
        return

    dfs_list = [pd.read_csv(f) for f in dfs_files]
    dfs_df = pd.concat(dfs_list, ignore_index=True)
    
    # 3. Mesclar dados e ordenar pelas instâncias
    merged_df = pd.merge(
        greedy_df[['arquivo', 'tempo_s']], 
        dfs_df[['arquivo', 'tempo_s', 'nos_explorados']], 
        on='arquivo', 
        suffixes=('_greedy', '_dfs')
    )
    merged_df = merged_df.sort_values('arquivo')
    
    # Limpeza estética: remove o '.txt' para o eixo X
    merged_df['instancia'] = merged_df['arquivo'].str.replace('.txt', '', regex=False)
    
    # Dimensions (5.5 x 4) ideais para colunas de papers IEEE/SBC
    
    # --- IMAGEM 1: Tempo de Execução Absoluto ---
    plt.figure(figsize=(5.5, 4))
    plt.plot(merged_df['instancia'], merged_df['tempo_s_greedy'], 
             label='Greedy', marker='o', color='#2ca02c', linewidth=1.5, markersize=4)
    plt.plot(merged_df['instancia'], merged_df['tempo_s_dfs'], 
             label='DFS + SumDegree (Timeout)', marker='x', color='#d62728', linestyle='--', linewidth=1.5, markersize=4)
    
    plt.yscale('log')
    plt.ylabel('Tempo de Execução (s) - Escala Log', fontsize=10)
    plt.xlabel('Instâncias', fontsize=10)
    plt.grid(True, which="both", ls="--", alpha=0.4)
    plt.legend(fontsize=9, loc='upper left')
    plt.xticks(rotation=90, fontsize=7)
    
    ax1 = plt.gca()
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    plt.title('Tempo de Execução Absoluto', fontsize=11, fontweight='bold', pad=10)
    
    plt.tight_layout()
    file_tempo = os.path.join(script_dir, 'tempo_execucao.png')
    plt.savefig(file_tempo, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Primeira imagem salva em: {file_tempo}")
    
    # --- IMAGEM 2: Esforço Computacional ---
    plt.figure(figsize=(5.5, 4))
    plt.bar(merged_df['instancia'], merged_df['nos_explorados'], 
            color='#4C72B0', alpha=0.85, edgecolor='black', linewidth=0.5)
    
    plt.ylabel('Total de Nós Explorados', fontsize=10)
    plt.xlabel('Instâncias', fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.4)
    plt.xticks(rotation=90, fontsize=7)
    
    ax2 = plt.gca()
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    plt.title('Esforço de Busca na Árvore do B&B', fontsize=11, fontweight='bold', pad=10)
    
    plt.tight_layout()
    file_nos = os.path.join(script_dir, 'nos_explorados.png')
    plt.savefig(file_nos, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Segunda imagem salva em: {file_nos}")

if __name__ == '__main__':
    main()
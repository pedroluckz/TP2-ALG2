import time
from Structures import SetCoverInstance
from BranchBound import GreedyUB, SumDegreeLB, DFS, BestFirst, PackingLB

def realizar_teste_sanidade():
    print("Iniciando Teste de Sanidade - Branch and Bound")
    
    # 1. Cria a instância
    instancia = SetCoverInstance(0, 0) # Valores serão sobrescritos na leitura
    
    try:
        instancia.load_from_file("scp41.txt")
        print(f"Arquivo carregado! Elementos: {instancia.num_elements}, Conjuntos: {instancia.num_sets}")
    except FileNotFoundError:
        print("Erro: Baixe o arquivo scp41.txt da OR-Library e coloque na mesma pasta.")
        return

    # 2. Monta as estratégias
    ub = GreedyUB()
    lb = SumDegreeLB() 
    lb1 = PackingLB() 
    
    dfs = DFS()
    bf = BestFirst()


    # 3. Executa e cronometra
    # DFS com SumDegreeLB e GreedyUB
    start_time = time.time()
    custo, solucao, nos = dfs.solve(instancia, ub, lb)
    end_time = time.time()


    print("\n--- RESULTADOS DFS---")
    print(f"Custo Ótimo Encontrado: {custo}")
    print(f"Total de Nós Explorados: {nos}")
    print(f"Tempo de Execução: {end_time - start_time:.4f} segundos")

    # Best-First com SumDegreeLB e GreedyUB
    start_time1 = time.time()
    custo1, solucao1, nos1 = bf.solve(instancia, ub, lb)
    end_time1 = time.time()


    print(f"\n--- RESULTADOS - Best-First ---")
    print(f"Custo Ótimo Encontrado: {custo1}")
    print(f"Total de Nós Explorados: {nos1}")
    print(f"Tempo de Execução: {end_time1 - start_time1:.4f} segundos")

if __name__ == "__main__":
    realizar_teste_sanidade()
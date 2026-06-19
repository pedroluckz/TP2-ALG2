import time
import os
import csv
import resource
from Structures import SetCoverInstance
from BranchBound import GreedyUB, SumDegreeLB, DFS, BestFirst, PackingLB

# ============================================================
# CONFIGURAÇÕES
# ============================================================
INSTANCES_ROOT = "OR_instances"   # pasta raiz com as instâncias
TIME_LIMIT     = 7200                    # segundos por execução (0 = sem limite)

# Nomes dos CSVs de saída
CSV_FILES = {
    "greedy":       "results_1_greedy.csv",
    "dfs_packing":  "results_2_dfs_packingLB.csv",
    "dfs_sumdeg":   "results_3_dfs_sumdegreeLB.csv",
    "bf_packing":   "results_4_bestfirst_packingLB.csv",
    "bf_sumdeg":    "results_5_bestfirst_sumdegreeLB.csv",
}

HEADERS_EXACT  = ["arquivo", "densidade", "m", "n", "status", "custo", "tempo_s"]
HEADERS_BB = ["arquivo", "densidade", "m", "n", "status", "custo", "nos_explorados", "nos_podados", "memoria_mb", "tempo_s"]

# ============================================================
# DESCOBERTA DE INSTÂNCIAS
# ============================================================
def discover_instances(root: str) -> list[dict]:
    """
    Percorre a árvore de pastas e retorna uma lista de dicts com
    {path, filename, density, m_hint, n_hint}.
    Estrutura esperada:  root / d<density> / m<M>_n<N> / *.txt
    """
    instances = []
    for density_dir in sorted(os.listdir(root)):
        density_path = os.path.join(root, density_dir)
        if not os.path.isdir(density_path):
            continue
        # Extrai densidade do nome da pasta (ex: d0.1 → "0.1")
        density = density_dir.lstrip("d")

        for size_dir in sorted(os.listdir(density_path)):
            size_path = os.path.join(density_path, size_dir)
            if not os.path.isdir(size_path):
                continue
            # Extrai m e n do nome da subpasta (ex: m200_n400)
            try:
                parts  = size_dir.split("_")
                m_hint = int(parts[0][1:])
                n_hint = int(parts[1][1:])
            except (IndexError, ValueError):
                m_hint = None
                n_hint = None

            for fname in sorted(os.listdir(size_path)):
                if fname.endswith(".txt"):
                    instances.append({
                        "path":     os.path.join(size_path, fname),
                        "filename": fname,
                        "density":  density,
                        "m_hint":   m_hint,
                        "n_hint":   n_hint,
                    })
    return instances

# ============================================================
# CARREGAMENTO DE INSTÂNCIA
# ============================================================
def load_instance(info: dict) -> SetCoverInstance:
    inst = SetCoverInstance(0, 0)
    inst.load_from_file(info["path"])
    return inst

# ============================================================
# EXECUÇÃO COM LIMITE DE TEMPO (wrapper simples via alarme UNIX)
# ============================================================
import signal

class TimeoutError(Exception):
    pass

def _handler(signum, frame):
    raise TimeoutError()

def run_with_timeout(fn, timeout_s):
    """
    Executa fn() com limite de tempo.  Retorna (result, timed_out).
    Se timeout_s <= 0, sem limite.
    Atenção: signal.alarm só funciona em UNIX; no Windows será ignorado.
    """
    if timeout_s > 0 and hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, _handler)
        signal.alarm(int(timeout_s))
    try:
        result = fn()
        if timeout_s > 0 and hasattr(signal, "SIGALRM"):
            signal.alarm(0)
        return result, False
    except TimeoutError:
        return None, True

# ============================================================
# ABORDAGEM 1 – GREEDY APROXIMATIVO
# ============================================================
def run_greedy(inst: SetCoverInstance, info: dict) -> dict:
    t0 = time.time()
    custo, _ = inst.calculate_greedy_upper_bound()
    elapsed = time.time() - t0
    return {
        "arquivo":   info["filename"],
        "densidade": info["density"],
        "m":         inst.num_elements,
        "n":         inst.num_sets,
        "status":    "OPTIMAL",
        "custo":     custo,
        "tempo_s":   round(elapsed, 6),
    }

# ============================================================
# ABORDAGEM 2-5 – BRANCH AND BOUND (DFS / Best-First)
# ============================================================
def run_bb(inst: SetCoverInstance, info: dict, solver_cls, lb_cls) -> dict:
    ub_strat = GreedyUB()
    lb_strat = lb_cls()
    solver   = solver_cls()

    # Prepara as variáveis de resgate (Caixa Preta)
    solver.partial_cost = "N/A"
    solver.partial_nodes = "N/A"
    solver.nodes_pruned = "N/A" # <-- NOVO RASTREADOR DE PODA

    t0 = time.time()
    status = "OPTIMAL"
    
    try:
        result, timed_out = run_with_timeout(lambda: solver.solve(inst, ub_strat, lb_strat), TIME_LIMIT)
        if timed_out:
            status = "TIMEOUT"
            
    except MemoryError:
        status = "OUT_OF_MEMORY"
    except Exception as e:
        status = f"ERRO"

    elapsed = time.time() - t0

    # Rastreia o pico exato de memória RAM consumida pelo Linux (em Megabytes)
    try:
        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        mem_mb = round(mem_kb / 1024.0, 2)
    except:
        mem_mb = "N/A" # Fallback caso rode no Windows acidentalmente

    return {
        "arquivo":        info["filename"],
        "densidade":      info["density"],
        "m":              inst.num_elements,
        "n":              inst.num_sets,
        "status":         status,
        "custo":          solver.partial_cost,
        "nos_explorados": solver.partial_nodes,
        "nos_podados":    solver.nodes_pruned,  # <-- SALVANDO A PODA
        "memoria_mb":     mem_mb,               # <-- SALVANDO A RAM
        "tempo_s":        round(elapsed, 6),
    }

    # def _solve():
    #     return solver.solve(inst, ub_strat, lb_strat)

    # t0 = time.time()
    # result, timed_out = run_with_timeout(_solve, TIME_LIMIT)
    # elapsed = time.time() - t0

    # if timed_out or result is None:
    #     custo = "TIMEOUT"
    #     nos   = "N/A"
    # else:
    #     custo, _, nos = result

    # return {
    #     "arquivo":        info["filename"],
    #     "densidade":      info["density"],
    #     "m":              inst.num_elements,
    #     "n":              inst.num_sets,
    #     "custo":          custo,
    #     "nos_explorados": nos,
    #     "tempo_s":        round(elapsed, 6),
    # }

# ============================================================
# UTILITÁRIO – escrita CSV incremental
# ============================================================
def append_csv(filepath: str, row: dict, headers: list):
    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("  EXPERIMENTO SET COVER – 5 ABORDAGENS")
    print("=" * 60)

    instances = discover_instances(INSTANCES_ROOT)
    total = len(instances)
    print(f"Instâncias encontradas: {total}\n")

    for i, info in enumerate(instances, 1):
        print(f"[{i:>4}/{total}] {info['density']} | {info['filename']}")

        inst = load_instance(info)

        # ---- 1. Greedy ----
        # row = run_greedy(inst, info)
        # append_csv(CSV_FILES["greedy"], row, HEADERS_EXACT)
        # print(f"         Greedy        → custo={row['custo']}  t={row['tempo_s']}s")

        # ---- 2. DFS + PackingLB ----
        # row = run_bb(inst, info, DFS, PackingLB)
        # append_csv(CSV_FILES["dfs_packing"], row, HEADERS_BB)
        # print(f"         DFS+Packing   → custo={row['custo']}  nós={row['nos_explorados']}  t={row['tempo_s']}s")

        # ---- 3. DFS + SumDegreeLB ----
        row = run_bb(inst, info, DFS, SumDegreeLB)
        append_csv(CSV_FILES["dfs_sumdeg"], row, HEADERS_BB)
        print(f"         DFS+SumDeg    → custo={row['custo']}  nós={row['nos_explorados']}  t={row['tempo_s']}s")

        # ---- 4. Best-First + PackingLB ----
        # row = run_bb(inst, info, BestFirst, PackingLB)
        # append_csv(CSV_FILES["bf_packing"], row, HEADERS_BB)
        # print(f"         BF+Packing    → custo={row['custo']}  nós={row['nos_explorados']}  t={row['tempo_s']}s")

        # ---- 5. Best-First + SumDegreeLB ----
        # row = run_bb(inst, info, BestFirst, SumDegreeLB)
        # append_csv(CSV_FILES["bf_sumdeg"], row, HEADERS_BB)
        # print(f"         BF+SumDeg     → custo={row['custo']}  nós={row['nos_explorados']}  t={row['tempo_s']}s")

        print()

    print("=" * 60)
    print("Resultados salvos em:")
    for key, path in CSV_FILES.items():
        print(f"  {path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
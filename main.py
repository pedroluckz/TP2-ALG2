import time
import os
import csv
import signal
import resource
from Structures import SetCoverInstance
from BranchBound import GreedyUB, SumDegreeLB, DFS, BestFirst, PackingLB

# CONFIGURAÇÕES

GENERATED_ROOT  = "generated_instances"  # pasta estruturada: d<x>/m<M>_n<N>/*.txt
OR_LIBRARY_ROOT = "OR_instances"         # pasta plana com arquivos OR-Library

TIME_LIMIT_GENERATED = 1800  # segundos por execução – instâncias geradas
TIME_LIMIT_OR        = 7200  # segundos por execução – OR-Library

# Pastas de saída
DIR_GENERATED = "testresults"
DIR_OR        = "OR_results"
os.makedirs(DIR_GENERATED, exist_ok=True)
os.makedirs(DIR_OR,        exist_ok=True)

# Nomes dos CSVs de saída – instâncias geradas (5 métodos)
CSV_FILES = {
    "greedy":      os.path.join(DIR_GENERATED, "results_1_greedy.csv"),
    "dfs_packing": os.path.join(DIR_GENERATED, "results_2_dfs_packingLB.csv"),
    "dfs_sumdeg":  os.path.join(DIR_GENERATED, "results_3_dfs_sumdegreeLB.csv"),
    "bf_packing":  os.path.join(DIR_GENERATED, "results_4_bestfirst_packingLB.csv"),
    "bf_sumdeg":   os.path.join(DIR_GENERATED, "results_5_bestfirst_sumdegreeLB.csv"),
}

# CSVs separados para OR-Library
CSV_OR = {
    "greedy":       os.path.join(DIR_OR, "or_results_1_greedy.csv"),
    "dfs_sumdeg_a": os.path.join(DIR_OR, "or_results_2a_dfs_sumdegreeLB_inst01_11.csv"),  # instancias  1-11
    "dfs_sumdeg_b": os.path.join(DIR_OR, "or_results_2b_dfs_sumdegreeLB_inst12_23.csv"),  # instancias 12-23
    "dfs_sumdeg_c": os.path.join(DIR_OR, "or_results_2c_dfs_sumdegreeLB_inst24_34.csv"),  # instancias 24-34
    "dfs_sumdeg_d": os.path.join(DIR_OR, "or_results_2d_dfs_sumdegreeLB_inst35_40.csv"),  # instancias 35-45
}

HEADERS_EXACT = ["arquivo", "densidade", "m", "n", "status", "custo", "tempo_s"]
HEADERS_BB    = ["arquivo", "densidade", "m", "n", "status", "custo",
                 "nos_explorados", "nos_podados", "memoria_mb", "tempo_s"]

# descoberta de instâncias geradas (estrutura de pastas original)
def discover_instances(root: str) -> list[dict]:

    # Estrutura esperada:  root / d<density> / m<M>_n<N> / *.txt
    # Densidade e tamanho são extraídos do nome das pastas.
    instances = []
    for density_dir in sorted(os.listdir(root)):
        density_path = os.path.join(root, density_dir)
        if not os.path.isdir(density_path):
            continue
        density = density_dir.lstrip("d")

        for size_dir in sorted(os.listdir(density_path)):
            size_path = os.path.join(density_path, size_dir)
            if not os.path.isdir(size_path):
                continue
            try:
                parts  = size_dir.split("_")
                m_hint = int(parts[0][1:])
                n_hint = int(parts[1][1:])
            except (IndexError, ValueError):
                m_hint = n_hint = None

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



# descoberta de instâncias OR-Library (pasta plana)

def parse_or_library_header(filepath: str) -> tuple[int, int, str]:

    # Extrai m, n e densidade diretamente do conteúdo do arquivo.
    
    # Densidade calculada como total_coberturas / (m * n).

    with open(filepath, "r") as f:
        tokens = f.read().split()

    idx = 0
    m = int(tokens[idx]); idx += 1
    n = int(tokens[idx]); idx += 1

    # Pula os n custos
    idx += n

    # Percorre as m linhas de cobertura somando o total de arcos
    total_covers = 0
    for _ in range(m):
        k = int(tokens[idx]); idx += 1
        total_covers += k
        idx += k  # pula os k índices de coluna

    density = total_covers / (m * n) if (m * n) > 0 else 0.0
    return m, n, f"{density:.4f}"


def discover_or_library_instances(root: str) -> list[dict]:
    instances = []
    for fname in sorted(os.listdir(root)):
        if not fname.endswith(".txt"):
            continue
        fpath = os.path.join(root, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            m, n, density = parse_or_library_header(fpath)
        except Exception as e:
            print(f"  [AVISO] Não foi possível ler o cabeçalho de {fname}: {e}")
            continue
        instances.append({
            "path":     fpath,
            "filename": fname,
            "density":  density,
            "m_hint":   m,
            "n_hint":   n,
        })
    return instances

# carregamento de instância

def load_instance(info: dict) -> SetCoverInstance:
    inst = SetCoverInstance(0, 0)
    inst.load_from_file(info["path"])
    return inst



# limite de tempo

class TimeoutError(Exception):
    pass

def _handler(signum, frame):
    raise TimeoutError()

def run_with_timeout(fn, timeout_s):
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

# runners

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


def run_bb(inst: SetCoverInstance, info: dict, solver_cls, lb_cls, time_limit: int) -> dict:
    ub_strat = GreedyUB()
    lb_strat = lb_cls()
    solver   = solver_cls()

    solver.partial_cost  = "N/A"
    solver.partial_nodes = "N/A"
    solver.nodes_pruned  = "N/A"

    t0     = time.time()
    status = "OPTIMAL"

    try:
        result, timed_out = run_with_timeout(
            lambda: solver.solve(inst, ub_strat, lb_strat), time_limit
        )
        if timed_out:
            status = "TIMEOUT"
    except MemoryError:
        status = "OUT_OF_MEMORY"
    except Exception:
        status = "ERRO"

    elapsed = time.time() - t0

    try:
        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        mem_mb = round(mem_kb / 1024.0, 2)
    except Exception:
        mem_mb = "N/A"

    return {
        "arquivo":        info["filename"],
        "densidade":      info["density"],
        "m":              inst.num_elements,
        "n":              inst.num_sets,
        "status":         status,
        "custo":          solver.partial_cost,
        "nos_explorados": solver.partial_nodes,
        "nos_podados":    solver.nodes_pruned,
        "memoria_mb":     mem_mb,
        "tempo_s":        round(elapsed, 6),
    }



# escrita CSV incremental

def append_csv(filepath: str, row: dict, headers: list):
    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)



# main

def main():

    # BLOCO 1 – instâncias geradas (5 métodos)
    print("=" * 60)
    print("  INSTÂNCIAS GERADAS – 5 MÉTODOS")
    print("=" * 60)

    gen_instances = discover_instances(GENERATED_ROOT)
    total = len(gen_instances)
    print(f"Instâncias encontradas: {total}\n")

    for i, info in enumerate(gen_instances, 1):
        print(f"[{i:>4}/{total}] {info['density']} | {info['filename']}")

        inst = load_instance(info)

        # 1. Greedy
        row = run_greedy(inst, info)
        append_csv(CSV_FILES["greedy"], row, HEADERS_EXACT)
        print(f"         Greedy        → custo={row['custo']}  t={row['tempo_s']}s")

        # 2. DFS + PackingLB
        row = run_bb(inst, info, DFS, PackingLB, TIME_LIMIT_GENERATED)
        append_csv(CSV_FILES["dfs_packing"], row, HEADERS_BB)
        print(f"         DFS+Packing   → custo={row['custo']}  nós={row['nos_explorados']}  t={row['tempo_s']}s")

        # 3. DFS + SumDegreeLB
        row = run_bb(inst, info, DFS, SumDegreeLB, TIME_LIMIT_GENERATED)
        append_csv(CSV_FILES["dfs_sumdeg"], row, HEADERS_BB)
        print(f"         DFS+SumDeg    → custo={row['custo']}  nós={row['nos_explorados']}  t={row['tempo_s']}s")

        # 4. Best-First + PackingLB
        row = run_bb(inst, info, BestFirst, PackingLB, TIME_LIMIT_GENERATED)
        append_csv(CSV_FILES["bf_packing"], row, HEADERS_BB)
        print(f"         BF+Packing    → custo={row['custo']}  nós={row['nos_explorados']}  t={row['tempo_s']}s")

        # 5. Best-First + SumDegreeLB
        row = run_bb(inst, info, BestFirst, SumDegreeLB, TIME_LIMIT_GENERATED)
        append_csv(CSV_FILES["bf_sumdeg"], row, HEADERS_BB)
        print(f"         BF+SumDeg     → custo={row['custo']}  nós={row['nos_explorados']}  t={row['tempo_s']}s")

        print()

    # BLOCO 2 – instâncias OR-Library (Greedy + DFS+SumDegreeLB)
    print("=" * 60)
    print("  OR-LIBRARY – GREEDY + DFS+SumDegreeLB")
    print("=" * 60)

    or_instances = discover_or_library_instances(OR_LIBRARY_ROOT)
    total_or = len(or_instances)
    print(f"Instâncias OR-Library encontradas: {total_or}\n")

    # Função auxiliar para rodar uma fatia das instâncias OR-Library.
    
    def run_or_slice(label, csv_key, start, end):
        """start e end são índices 1-based, inclusivos."""
        sl = or_instances[start - 1 : end]
        print(f"  [{label}] instâncias {start}–{end} ({len(sl)} arquivos)")
        for i, info in enumerate(sl, start):
            print(f"  [{i:>2}/{total_or}] {info['filename']}  densidade={info['density']}  m={info['m_hint']}  n={info['n_hint']}")
            try:
                inst = load_instance(info)
            except Exception as e:
                print(f"         [ERRO ao carregar] {e}\n")
                continue
            row = run_bb(inst, info, DFS, SumDegreeLB, TIME_LIMIT_OR)
            append_csv(CSV_OR[csv_key], row, HEADERS_BB)
            print(f"         DFS+SumDeg → status={row['status']}  custo={row['custo']}  nós={row['nos_explorados']}  podados={row['nos_podados']}  mem={row['memoria_mb']}MB  t={row['tempo_s']}s")
            print()

    # OR Greedy (todas as instâncias)
    print("--- Greedy (todas) ---")
    for i, info in enumerate(or_instances, 1):
        print(f"  [{i:>2}/{total_or}] {info['filename']}")
        try:
            inst = load_instance(info)
        except Exception as e:
            print(f"         [ERRO ao carregar] {e}\n")
            continue
        row = run_greedy(inst, info)
        append_csv(CSV_OR["greedy"], row, HEADERS_EXACT)
        print(f"         Greedy → custo={row['custo']}  t={row['tempo_s']}s")
    print()

    # OR DFS+SumDegreeLB – instâncias  1 a 11
    run_or_slice("A", "dfs_sumdeg_a", 1, 11)

    # OR DFS+SumDegreeLB – instâncias 12 a 23
    run_or_slice("B", "dfs_sumdeg_b", 12, 23)

    # OR DFS+SumDegreeLB – instâncias 24 a 34
    run_or_slice("C", "dfs_sumdeg_c", 33, 34)

    # OR DFS+SumDegreeLB – instâncias 35 a 45
    run_or_slice("D", "dfs_sumdeg_d", 35,45)

    # SUMÁRIO FINAL
    print("=" * 60)
    print("Resultados salvos em:")
    print("  [Instâncias Geradas]")
    for path in CSV_FILES.values():
        print(f"    {path}")
    print("  [OR-Library]")
    for path in CSV_OR.values():
        print(f"    {path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
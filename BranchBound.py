from abc import ABC, abstractmethod
import heapq
import math
import time
from Structures import SetCoverInstance

# ==========================================
# 1. ESTRATÉGIAS DE LIMITE SUPERIOR (UPPER BOUND)
# ==========================================
class UpperBound(ABC):
    @abstractmethod
    def calculate(self, instance: SetCoverInstance) -> tuple[float, list]:
        pass

class TrivialUB(UpperBound):
    def calculate(self, instance: SetCoverInstance):
        # Solução trivial: pega absolutamente todos os conjuntos disponíveis
        custo_total = sum(instance.costs)
        todos_os_conjuntos = list(range(instance.num_sets))
        return custo_total, todos_os_conjuntos

class GreedyUB(UpperBound):
    def calculate(self, instance: SetCoverInstance):
        return instance.calculate_greedy_upper_bound()

# ==========================================
# 2. ESTRATÉGIAS DE LIMITE INFERIOR (LOWER BOUND)
# ==========================================
class LowerBound(ABC):
    def __init__(self):
        self.ordered_indices = None
        
    def set_mapping(self, instance: SetCoverInstance, ordered_indices: list):
        self.ordered_indices = ordered_indices

    @abstractmethod
    def calculate(self, instance: SetCoverInstance, current_cost: float, covered_mask: int, next_idx: int) -> float:
        pass

class TrivialLB(LowerBound):
    def calculate(self, instance: SetCoverInstance, current_cost: float, covered_mask: int, next_idx: int) -> float:
        # Se cobriu tudo, custa 0. Se não cobriu, o estimador "burro" também diz que custa 0.
        # Isso efetivamente desliga a poda do Branch-and-Bound, transformando-o em Força Bruta.
        uncovered_mask = instance.base_mask & ~covered_mask
        if uncovered_mask == 0:
            return 0
        return 0.0

class SumDegreeLB(LowerBound):
    def __init__(self):
        super().__init__()
        self.max_deg_suffix = []
        self.min_cost_suffix = []
        self.or_suffix = []

    def set_mapping(self, instance: SetCoverInstance, ordered_indices: list):
        super().set_mapping(instance, ordered_indices)
        n = instance.num_sets

        self.max_deg_suffix = [0] * (n + 1)
        self.min_cost_suffix = [0] * (n + 1)
        self.or_suffix = [0] * (n + 1)

        current_max = 0
        current_min_cost = float('inf')
        current_or = 0

        # Pré-calcula tudo de trás para frente usando a ORDEM da Busca
        for i in range(n - 1, -1, -1):
            real_idx = ordered_indices[i]
            mask = instance.sets_masks[real_idx]
            cost = instance.costs[real_idx]

            deg = mask.bit_count() 
            if deg > current_max: current_max = deg
            if cost < current_min_cost: current_min_cost = cost
            current_or |= mask

            self.max_deg_suffix[i] = current_max
            self.min_cost_suffix[i] = current_min_cost
            self.or_suffix[i] = current_or

    def calculate(self, instance, current_cost, covered_mask, next_idx):
        if next_idx >= instance.num_sets:
            return float('inf')
            
        # 1. A BALA DE PRATA: PODA DE VIABILIDADE
        # Verifica instantaneamente se os conjuntos restantes DÃO CONTA de cobrir o universo
        if (covered_mask | self.or_suffix[next_idx]) != instance.base_mask:
            return float('inf')

        # 2. PODA MATEMÁTICA SUM-DEGREE O(1)
        uncovered_mask = instance.base_mask & ~covered_mask
        elements_left = uncovered_mask.bit_count()
        
        if elements_left == 0:
            return 0
            
        max_deg = self.max_deg_suffix[next_idx]
        min_cost = self.min_cost_suffix[next_idx]
            
        if max_deg == 0:
            return float('inf')
            
        return math.ceil(elements_left / max_deg) * min_cost

# ==========================================
# 3. ESTRATÉGIAS DE TRAVESSIA (BRANCH AND BOUND)
# ==========================================
class DFS:
    def solve(self, instance: SetCoverInstance, ub_strategy: UpperBound, lb_strategy: LowerBound):
        best_cost, best_solution = ub_strategy.calculate(instance)
        print(f"[*] Inicializando Branch & Bound com DFS...")
        print(f"[*] Custo Inicial do Guloso (Teto): {best_cost}")
        
        ordered_indices = list(range(instance.num_sets))
        ordered_indices.sort(key=lambda idx: instance.costs[idx] / max(1, instance.sets_masks[idx].bit_count()))
        
        lb_strategy.set_mapping(instance, ordered_indices)

        stack = [(0, 0, 0, [])]
        nodes_visited = 0
        
        # --- CONFIGURAÇÃO DO LIMITADOR ---
        start_time = time.time()
        TIME_LIMIT = 120  # 2 minutos (você pode ajustar para 300 depois para testes maiores)

        while stack:
            current_cost, covered_mask, next_set_idx, selected_sets = stack.pop()
            nodes_visited += 1

            # Monitor de Progresso (Feedback Visual)
            if nodes_visited % 500000 == 0:
                decorrido = time.time() - start_time
                print(f"   -> Progresso: {nodes_visited} nós explorados em {decorrido:.1f}s | Melhor custo: {best_cost}")

            # Ejetor de Segurança (Time Limit)
            if time.time() - start_time > TIME_LIMIT:
                print(f"\n[!] LIMITADOR DE TEMPO ATIVADO ({TIME_LIMIT}s). Abortando a busca...")
                break

            if covered_mask == instance.base_mask:
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_solution = selected_sets
                    print(f"[*] Novo melhor custo encontrado: {best_cost}")
                continue

            if next_set_idx >= instance.num_sets:
                continue

            lb = lb_strategy.calculate(instance, current_cost, covered_mask, next_set_idx)

            if current_cost + lb >= best_cost:
                continue

            real_idx = ordered_indices[next_set_idx]
            set_mask = instance.sets_masks[real_idx]
            set_cost = instance.costs[real_idx]

            stack.append((current_cost, covered_mask, next_set_idx + 1, selected_sets))

            new_elements = set_mask & ~covered_mask
            if new_elements > 0:
                stack.append((
                    current_cost + set_cost,
                    covered_mask | set_mask,
                    next_set_idx + 1,
                    selected_sets + [real_idx]
                ))

        return best_cost, best_solution, nodes_visited

class BestFirst:
    def solve(self, instance: SetCoverInstance, ub_strategy: UpperBound, lb_strategy: LowerBound):
        best_cost, best_solution = ub_strategy.calculate(instance)
        print(f"[*] Inicializando Branch & Bound com Best-First...")
        print(f"[*] Custo Inicial do Guloso (Teto): {best_cost}")
        
        ordered_indices = list(range(instance.num_sets))
        ordered_indices.sort(key=lambda idx: instance.costs[idx] / max(1, instance.sets_masks[idx].bit_count()))
        
        lb_strategy.set_mapping(instance, ordered_indices)

        pq = []
        nodes_visited = 0
        
        initial_lb = lb_strategy.calculate(instance, 0, 0, 0)
        if initial_lb < float('inf'):
            heapq.heappush(pq, (initial_lb, nodes_visited, 0, 0, 0, []))

        # --- CONFIGURAÇÃO DO LIMITADOR ---
        start_time = time.time()
        # TIME_LIMIT = 120  # 2 minutos de limite

        while pq:
            priority, _, current_cost, covered_mask, next_idx, selected = heapq.heappop(pq)
            nodes_visited += 1

            # Monitor de Progresso (Feedback Visual)
            if nodes_visited % 500000 == 0:
                decorrido = time.time() - start_time
                print(f"   -> Progresso: {nodes_visited} nós explorados em {decorrido:.1f}s | Melhor custo: {best_cost}")

            # Ejetor de Segurança (Time Limit)
            # if time.time() - start_time > TIME_LIMIT:
            #     print(f"\n[!] LIMITADOR DE TEMPO ATIVADO ({TIME_LIMIT}s). Abortando a busca Best-First...")
            #     break

            # Se a prioridade do MELHOR nó da fila já bateu no teto, acabou a busca!
            if priority >= best_cost:
                break

            if covered_mask == instance.base_mask:
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_solution = selected
                    print(f"[*] Novo melhor custo encontrado: {best_cost}")
                continue

            if next_idx >= instance.num_sets:
                continue

            real_idx = ordered_indices[next_idx]
            set_mask = instance.sets_masks[real_idx]
            set_cost = instance.costs[real_idx]

            lb_without = lb_strategy.calculate(instance, current_cost, covered_mask, next_idx + 1)
            if current_cost + lb_without < best_cost:
                heapq.heappush(pq, (current_cost + lb_without, nodes_visited + 1, current_cost, covered_mask, next_idx + 1, selected))

            new_elements = set_mask & ~covered_mask
            if new_elements > 0:
                new_cost = current_cost + set_cost
                new_covered = covered_mask | set_mask
                lb_with = lb_strategy.calculate(instance, new_cost, new_covered, next_idx + 1)
                
                if new_cost + lb_with < best_cost:
                    heapq.heappush(pq, (new_cost + lb_with, nodes_visited + 2, new_cost, new_covered, next_idx + 1, selected + [real_idx]))

        return best_cost, best_solution, nodes_visited
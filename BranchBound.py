import heapq
import math
import time
from Structures import SetCoverInstance

# ==========================================
# 1. ESTRATÉGIAS DE LIMITE SUPERIOR (UPPER BOUND)
# ==========================================
class UpperBound:
    def calculate(self, instance: SetCoverInstance) -> tuple[float, list]:
        pass


class GreedyUB(UpperBound):
    def calculate(self, instance: SetCoverInstance):
        return instance.calculate_greedy_upper_bound()

# ==========================================
# 2. ESTRATÉGIAS DE LIMITE INFERIOR (LOWER BOUND)
# ==========================================
class LowerBound:
    def __init__(self):
        self.ordered_indices = None
        
    def set_mapping(self, instance: SetCoverInstance, ordered_indices: list):
        self.ordered_indices = ordered_indices

    def calculate(self, instance: SetCoverInstance, current_cost: float, covered_mask: int, next_idx: int) -> float:
        pass

    
class PackingLB(LowerBound):
    def __init__(self):
        super().__init__()
        self.or_suffix = []

    def set_mapping(self, instance: SetCoverInstance, ordered_indices: list):
        super().set_mapping(instance, ordered_indices)
        n = instance.num_sets
        self.or_suffix = [0] * (n + 1)
        
        current_or = 0
        # Pré-calcula a poda de viabilidade de trás para frente
        for i in range(n - 1, -1, -1):
            real_idx = ordered_indices[i]
            current_or |= instance.sets_masks[real_idx]
            self.or_suffix[i] = current_or

    def calculate(self, instance, current_cost, covered_mask, next_idx):
        if next_idx >= instance.num_sets:
            return float('inf')
            
        # 1. Poda de Viabilidade O(1) (NUNCA tire isso, é a sua rede de segurança)
        if (covered_mask | self.or_suffix[next_idx]) != instance.base_mask:
            return float('inf')

        # 2. Packing Lower Bound (Grafo de Conflitos via Bits)
        uncovered = instance.base_mask & ~covered_mask
        if uncovered == 0:
            return 0
            
        valid_elements = uncovered
        lb_added = 0
        
        while valid_elements > 0:
            # Truque clássico de baixo nível: isola o bit '1' mais à direita (o primeiro elemento válido)
            e_mask = valid_elements & -valid_elements
            
            min_cost_e = float('inf')
            conflict_mask = 0
            
            # Varre os conjuntos disponíveis para construir o grafo de conflito desse elemento
            for i in range(next_idx, instance.num_sets):
                real_idx = self.ordered_indices[i]
                s_mask = instance.sets_masks[real_idx]
                
                # Se este conjunto cobre o nosso elemento 'e'
                if s_mask & e_mask:
                    cost = instance.costs[real_idx]
                    if cost < min_cost_e:
                        min_cost_e = cost
                    
                    # Adiciona esse conjunto inteiro à máscara de conflito
                    conflict_mask |= s_mask
                    
            if min_cost_e == float('inf'):
                # Existe um elemento que não pode mais ser coberto por NENHUM conjunto restante
                return float('inf')
                
            lb_added += min_cost_e
            
            # Remove do pool de candidatos o elemento 'e' e TODOS os seus vizinhos de conflito
            valid_elements &= ~conflict_mask
            
        return lb_added

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
        #TIME_LIMIT = 120  # 2 minutos (você pode ajustar para 300 depois para testes maiores)

        try:
            while stack:
                current_cost, covered_mask, next_set_idx, selected_sets = stack.pop()
                nodes_visited += 1

                # Monitor de Progresso (Feedback Visual)
                if nodes_visited % 500000 == 0:
                    decorrido = time.time() - start_time
                    print(f"   -> Progresso: {nodes_visited} nós explorados em {decorrido:.1f}s | Melhor custo: {best_cost}")

                # Ejetor de Segurança (Time Limit)
                # if time.time() - start_time > TIME_LIMIT:
                #     print(f"\n[!] LIMITADOR DE TEMPO ATIVADO ({TIME_LIMIT}s). Abortando a busca...")
                #     break

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
        except BaseException as e:
            # Se o processo for interrompido de forma violenta, ele guarda os dados no 'self' antes de morrer
            self.partial_cost = best_cost
            self.partial_nodes = nodes_visited
            raise e # Repassa a interrupção para a main.py
            
        # Se terminar naturalmente, também guarda os dados
        self.partial_cost = best_cost
        self.partial_nodes = nodes_visited

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

        try:
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
                
        except BaseException as e:
            # Se o processo for interrompido de forma violenta, ele guarda os dados no 'self' antes de morrer
            self.partial_cost = best_cost
            self.partial_nodes = nodes_visited
            raise e # Repassa a interrupção para a main.py
            
        # Se terminar naturalmente, também guarda os dados
        self.partial_cost = best_cost
        self.partial_nodes = nodes_visited
        return best_cost, best_solution, nodes_visited
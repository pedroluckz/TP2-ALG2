import heapq
import time
import resource
from Structures import SetCoverInstance

# Calcula o upper bound, nesse caso usando o algoritmo guloso
# chamado uma vez para obter o teto inicial
class UpperBound:
    def calculate(self, instance: SetCoverInstance) -> tuple[float, list]:
        pass


class GreedyUB(UpperBound):
    def calculate(self, instance: SetCoverInstance):
        return instance.calculate_greedy_upper_bound()

# Estrategias de lowerbound
class LowerBound:
    def __init__(self):
        self.ordered_indices = None

    # set_mapping é chamado uma vez no inicio da busca e fornece o mapeamento dos indices ordenados
    def set_mapping(self, instance: SetCoverInstance, ordered_indices: list):
        self.ordered_indices = ordered_indices

    # calculate é chamado para cada no visitado e retorna o lower bound daquele no
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
        # pre-calcula a poda de viabilidade de trás para frente
        for i in range(n - 1, -1, -1):
            real_idx = ordered_indices[i]
            # a mascara de união de todos os conjuntos restantes a partir de i
            # ou seja, encontra todos os elementos que podem ser cobertos a partir de i
            current_or |= instance.sets_masks[real_idx]
            self.or_suffix[i] = current_or

    def calculate(self, instance, current_cost, covered_mask, next_idx):
        # se já analisou todos os conjuntos e ainda falta cobrir algo, é inviável e poda o galho
        if next_idx >= instance.num_sets:
            return float('inf')
            
        # poda de viabilidade O(1)
        if (covered_mask | self.or_suffix[next_idx]) != instance.base_mask:
            return float('inf')

        # grafo de Conflitos usando os bits
        uncovered = instance.base_mask & ~covered_mask
        if uncovered == 0:
            return 0
            
        valid_elements = uncovered
        lb_add = 0
        
        while valid_elements > 0:
            # isola o bit '1' mais à direita q eh o primeiro elemento valido a ser coberto
            mask_aux = valid_elements & -valid_elements
            
            min_cost_aux = float('inf')
            conflict_mask = 0
            
            # varre os conjuntos disponíveis para construir o grafo de conflito desse elemento
            for i in range(next_idx, instance.num_sets):
                real_idx = self.ordered_indices[i]
                mask_set = instance.sets_masks[real_idx]
                
                # se este conjunto cobre o elemento auxiliar
                if mask_set & mask_aux:
                    cost = instance.costs[real_idx]
                    if cost < min_cost_aux:
                        min_cost_aux = cost
                    
                    # add esse conjunto inteiro na mascara de conflito
                    conflict_mask |= mask_set
                    
            if min_cost_aux == float('inf'):
                # se existe um elemento que não pode mais ser coberto por nenhum conj restante
                return float('inf')
                
            lb_add += min_cost_aux
            
            # remove dos candidatos o elemento auxiliar e os seus "vizinhos de conflito"
            valid_elements &= ~conflict_mask
            
        return lb_add

class SumDegreeLB(LowerBound):
    def __init__(self):
        super().__init__()
        self.or_suffix = []

    def set_mapping(self, instance: SetCoverInstance, ordered_indices: list):
        super().set_mapping(instance, ordered_indices)
        n = instance.num_sets
        self.or_suffix = [0] * (n + 1)
        
        current_or = 0
        # pre-calcula a poda de viabilidade padrão de trás para frente
        for i in range(n - 1, -1, -1):
            real_idx = ordered_indices[i]
            current_or |= instance.sets_masks[real_idx]
            self.or_suffix[i] = current_or

    def calculate(self, instance, current_cost, covered_mask, next_idx):
        if next_idx >= instance.num_sets:
            return float('inf')
            
        # poda de Viabilidade O(1)
        if (covered_mask | self.or_suffix[next_idx]) != instance.base_mask:
            return float('inf')

        # encontra o que ainda falta cobrir
        uncovered_mask = instance.base_mask & ~covered_mask
        elements_left = uncovered_mask.bit_count()
        
        if elements_left == 0:
            return 0

        # coleta o grau relevante de cada conjunto que resta na busca
        degrees = []
        for i in range(next_idx, instance.num_sets):
            real_idx = self.ordered_indices[i]
            #  conta apenas os bits úteis que este conjunto traz
            degree_aux = (instance.sets_masks[real_idx] & uncovered_mask).bit_count()
            if degree_aux > 0:
                degrees.append(degree_aux)
        
        # Ordena os graus de forma decrescente
        degrees.sort(reverse=True)
        
        total_covered = 0
        k = 0
        
        # procura o menor k onde a soma acumulada atinge ou passa os elementos restantes
        for degree_aux in degrees:
            total_covered += degree_aux
            k += 1
            if total_covered >= elements_left:
                return k
        
        # se a soma de todos os conjuntos restantes não consegue atingir o total, é inviável, poda o galho
        return float('inf')


# estratégias de busca
class DFS:
    def solve(self, instance: SetCoverInstance, ub_strategy: UpperBound, lb_strategy: LowerBound):
        # usa o algoritmo de ub para obter a solução inicial (teto) antes de iniciar a busca
        best_cost, best_solution = ub_strategy.calculate(instance)
        print(f"[*] Inicializando Branch & Bound com DFS...")
        print(f"[*] Custo Inicial do Guloso (Teto): {best_cost}")
        
        # Ordena os índices dos conjuntos com base no custo por elemento coberto
        ordered_indices = list(range(instance.num_sets))
        ordered_indices.sort(key=lambda idx: instance.costs[idx] / max(1, instance.sets_masks[idx].bit_count()))
        lb_strategy.set_mapping(instance, ordered_indices)

        # uso da pilha pra controlar da exploração em profundidade
        # estado do no:(custo_acumulado, mascara_coberta, indice_proximo_conjunto, conjuntos_selecionados)
        stack = [(0, 0, 0, [])]
        nodes_visited = 0
        self.nodes_pruned = 0  # inicializa o contador de nós podados
        start_time = time.time()

        try:
            while stack:
                current_cost, covered_mask, next_set_idx, selected_sets = stack.pop()
                nodes_visited += 1

                # feedback visual de que o algoritmo ta rodando
                if nodes_visited % 1000000 == 0:
                    time_passed = time.time() - start_time
                    print(f"   -> DFS: {nodes_visited} nós visitados | Podados: {self.nodes_pruned} | t={time_passed:.1f}s | Melhor custo: {best_cost}")

                # se uma soluçao viável foi encontrada
                if covered_mask == instance.base_mask:
                    if current_cost < best_cost:
                        best_cost = current_cost
                        best_solution = selected_sets
                        print(f"[*] Novo melhor custo encontrado: {best_cost}")
                    continue

                # fim das variaveis de decisao
                if next_set_idx >= instance.num_sets:
                    continue

                # usa o lb pra calcular o minimo necessario a ser gasto a partir desse no
                lb = lb_strategy.calculate(instance, current_cost, covered_mask, next_set_idx)

                # se o custo atual + lb for pior que o melhor encontrado, poda a árvore
                if current_cost + lb >= best_cost:
                    self.nodes_pruned += 1  # registra a poda
                    continue

                # identifica o proximo conjunto a ser analisado
                real_idx = ordered_indices[next_set_idx]
                set_mask = instance.sets_masks[real_idx]
                set_cost = instance.costs[real_idx]

                # analisa o galho "sem" o conjunto
                stack.append((current_cost, covered_mask, next_set_idx + 1, selected_sets))

                # analisa o galho "com" o conjunto
                new_elements = set_mask & ~covered_mask
                if new_elements > 0:
                    stack.append((
                        current_cost + set_cost,
                        covered_mask | set_mask,
                        next_set_idx + 1,
                        selected_sets + [real_idx]
                    ))
        # tratamento se tiver interrupçao pra salvar o progresso ate aqui
        except BaseException as e:
            self.partial_cost = best_cost
            self.partial_nodes = nodes_visited
            raise e 
            
        self.partial_cost = best_cost
        self.partial_nodes = nodes_visited
        return best_cost, best_solution, nodes_visited


class BestFirst:
    def solve(self, instance: SetCoverInstance, ub_strategy: UpperBound, lb_strategy: LowerBound):
        # usa o algoritmo de ub para obter a solução inicial (teto) antes de iniciar a busca
        best_cost, best_solution = ub_strategy.calculate(instance)
        print(f"[*] Inicializando Branch & Bound com Best-First...")
        print(f"[*] Custo Inicial do Guloso (Teto): {best_cost}")
        
        # ordena os índices dos conjuntos com base no custo por elemento coberto
        ordered_indices = list(range(instance.num_sets))
        ordered_indices.sort(key=lambda idx: instance.costs[idx] / max(1, instance.sets_masks[idx].bit_count()))
        lb_strategy.set_mapping(instance, ordered_indices)

        #o próximo nó a ser explorado eh sempre o que tem o menor custo total estimado, por isso a priority queue
        pq = []
        nodes_visited = 0
        self.nodes_pruned = 0
        
        # Calcula o limite inferior do nó raiz e insere na fila se for viável   
        initial_lb = lb_strategy.calculate(instance, 0, 0, 0)
        if initial_lb < float('inf'):
            heapq.heappush(pq, (initial_lb, nodes_visited, 0, 0, 0, []))

        start_time = time.time()

        try:
            while pq:
                # extrai o no com o menor custo total estimado (custo acumulado + lb)
                priority, _, current_cost, covered_mask, next_idx, selected = heapq.heappop(pq)
                nodes_visited += 1

                # feedback visual de que o algoritmo ta rodando certo
                if nodes_visited % 250000 == 0:
                    try:
                        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                        mem_mb = mem_kb / 1024.0
                    except:
                        mem_mb = 0.0 # caso de problema de compatibilidade
                        
                    tamanho_fila = len(pq)
                    time_passed = time.time() - start_time
                    print(f"   -> BF: {nodes_visited} nós | Podados: {self.nodes_pruned} | Fila: {tamanho_fila} itens | RAM: {mem_mb:.1f} MB | t={time_passed:.1f}s | Melhor custo: {best_cost}")

                # se o custo total estimado do melhor nó já é pior que o melhor encontrado, poda a árvore
                if priority >= best_cost:
                    break

                # se uma nova melhor soluçao foi encontrada
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

                # no ramo esquerdo: analisa o galho "sem" o conjunto
                lb_without = lb_strategy.calculate(instance, current_cost, covered_mask, next_idx + 1)
                if current_cost + lb_without < best_cost:
                    heapq.heappush(pq, (current_cost + lb_without, nodes_visited + 1, current_cost, covered_mask, next_idx + 1, selected))
                else:
                    self.nodes_pruned += 1 # registra a poda do galho

                # no ramo direito: analisa o galho "com" o conjunto
                new_elements = set_mask & ~covered_mask
                if new_elements > 0:
                    new_cost = current_cost + set_cost
                    new_covered = covered_mask | set_mask
                    lb_with = lb_strategy.calculate(instance, new_cost, new_covered, next_idx + 1)
                    
                    if new_cost + lb_with < best_cost:
                        # o custo total estimado desse nó é melhor que o melhor encontrado, então insere na fila para explorar depois
                        heapq.heappush(pq, (new_cost + lb_with, nodes_visited + 2, new_cost, new_covered, next_idx + 1, selected + [real_idx]))
                    else:
                        self.nodes_pruned += 1 # registra poda do galho
                
        # tratamento pra salvar o progresso ate aqui
        except BaseException as e:
            self.partial_cost = best_cost
            self.partial_nodes = nodes_visited
            raise e 
            
        self.partial_cost = best_cost
        self.partial_nodes = nodes_visited
        return best_cost, best_solution, nodes_visited
#from collections import namedtuple

class SetCoverInstance:
    def __init__(self, num_elements, num_sets):
        self.num_elements = num_elements
        self.num_sets = num_sets
        
        # a mascara base é um inteiro onde os 'num_elements' primeiros bits são 1
        self.base_mask = (1 << num_elements) - 1 
        
        # Lista armazenando o custo de cada conjunto
        self.costs = [] 
        
        # Lista armazenando a máscara de bits (inteiro) de cada conjunto
        self.sets_masks = [] 

    def load_from_file(self, filepath):
        with open(filepath, 'r') as f:
            tokens = f.read().split()

        pos = 0

        # m linhas, n colunas
        m = int(tokens[pos]); pos += 1
        n = int(tokens[pos]); pos += 1

        self.num_elements = m
        self.num_sets = n
        self.base_mask = (1 << m) - 1

        # custos
        self.costs = []

        ## Ignorando os pesos, coloca tudo como 1
        for _ in range(n):
            ignorar_custo = int(tokens[pos])  # O custo é lido, mas não usado na heurística gulosa
            pos += 1
            self.costs.append(1)

        # máscara de cada conjunto
        self.sets_masks = [0] * n

        # para cada elemento
        for row in range(m):

            k = int(tokens[pos])
            pos += 1

            for _ in range(k):

                col = int(tokens[pos])
                pos += 1

                # OR-Library usa índices começando em 1
                col -= 1

                # adiciona o elemento "row"
                self.sets_masks[col] |= (1 << row)


    def calculate_greedy_upper_bound(self):
        covered_mask = 0
        total_cost = 0
        selected_sets = []
        
        # Mantém uma lista dos conjuntos que ainda podem ser escolhidos
        available_sets = list(range(self.num_sets))
        
        # Continua enquanto não cobrir todos os bits (elementos) do universo
        while covered_mask != self.base_mask:
            best_set_idx = -1
            best_ratio = float('inf')
            
            for idx in available_sets:
                # A mágica da bitmask: o operador '~' inverte os bits cobertos.
                # O operador '&' cruza com a máscara do conjunto.
                # Resultado: apenas os elementos INÉDITOS que este conjunto cobre.
                new_elements_mask = self.sets_masks[idx] & ~covered_mask
                
                # .bit_count() conta quantos '1's existem no binário.
                # É nativo no Python 3.10+ e executado em C, extremamente rápido.
                new_elements_count = new_elements_mask.bit_count()
                
                if new_elements_count > 0:
                    # Calcula o custo-benefício (menor é melhor)
                    ratio = self.costs[idx] / new_elements_count
                    
                    if ratio < best_ratio:
                        best_ratio = ratio
                        best_set_idx = idx
            
            # Se não encontrou nenhum conjunto válido, a instância é inviável
            if best_set_idx == -1:
                return float('inf'), []
                
            # Atualiza o estado global marcando os novos elementos como cobertos
            covered_mask |= self.sets_masks[best_set_idx]
            total_cost += self.costs[best_set_idx]
            selected_sets.append(best_set_idx)
            
            # Remove o conjunto escolhido para não ser iterado novamente
            available_sets.remove(best_set_idx)
            
        return total_cost, selected_sets

# Usamos um namedtuple para o Nó da árvore para economizar memória
# current_cost: Custo acumulado até agora
# covered_mask: Inteiro representando os elementos já cobertos
# next_set_idx: Índice do próximo conjunto a ser avaliado (incluir ou não)
# selected_sets: Lista dos índices dos conjuntos selecionados até agora
#Node = namedtuple('Node', ['current_cost', 'covered_mask', 'next_set_idx', 'selected_sets'])


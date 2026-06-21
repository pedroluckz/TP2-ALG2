class SetCoverInstance:
    def __init__(self, num_elements, num_sets):
        self.num_elements = num_elements
        self.num_sets = num_sets
        
        # a mascara base é um inteiro onde os 'num_elements' primeiros bits são 1
        self.base_mask = (1 << num_elements) - 1 
        
        # lista armazenando o custo de cada conjunto
        self.costs = [] 
        
        # lista armazenando a mascara de bits de cada conjunto
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

        # ignorando os pesos, coloca tudo como 1
        for _ in range(n):
            ignorar_custo = int(tokens[pos])  # O custo é lido, mas não é usado
            pos += 1
            self.costs.append(1)

        # mascara de cada conjunto
        self.sets_masks = [0] * n

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
        
        # mantem uma lista dos conjuntos que ainda podem ser escolhidos
        available_sets = list(range(self.num_sets))
        
        # continua enquanto não cobrir todos os elementos do universo
        while covered_mask != self.base_mask:
            best_set_idx = -1
            best_cost = float('inf')
            
            for idx in available_sets:
                # inverte os bits cobertos (~) e faz o and com a mascara do conjunto pra descobrir quais elementos novos esse conjunto cobriria
                new_elements_mask = self.sets_masks[idx] & ~covered_mask
                
                # .bit_count() conta quantos 1's existem no binário.
                new_elements_count = new_elements_mask.bit_count()
                
                if new_elements_count > 0:
                    # calcula o custo-benefício (menor eh melhor)
                    cost_ratio = self.costs[idx] / new_elements_count
                    
                    if cost_ratio < best_cost:
                        best_cost = cost_ratio
                        best_set_idx = idx
            
            # se nao encontrou nenhum conjunto valido, a instância eh inviavel
            if best_set_idx == -1:
                return float('inf'), []
                
            # atualiza o estado global marcando os novos elementos como cobertos
            covered_mask |= self.sets_masks[best_set_idx]
            total_cost += self.costs[best_set_idx]
            selected_sets.append(best_set_idx)
            
            # remove o conjunto escolhido para não ser iterado novamente
            available_sets.remove(best_set_idx)
            
        return total_cost, selected_sets


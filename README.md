# Trabalho Prático II - Algoritmos II (DCC207)
Alice Lessa Ferreira <br>
Pedro Lucas Garcia Calais <br> <br>

# Problema de Cobertura de Conjuntos (Set Covering Problem)

Implementação e análise de desempenho de algoritmos aproximativos e exatos para a resolução da variante unicusto do Problema de Cobertura de Conjuntos (SCP).

## Como Executar

Para rodar o projeto, é necessário preparar as instâncias de teste:

Crie uma pasta chamada OR_instances no diretório raiz do projeto.

Baixe os arquivos de texto (.txt) das instâncias do SCP da OR-Library e coloque-os dentro dessa pasta.

Execute o arquivo principal via terminal:
python main.py

## Funcionamento

O sistema avalia as instâncias através de duas abordagens:

### Heurística Gulosa: 

Algoritmo aproximativo que encontra rapidamente uma solução inicial de alta qualidade para servir de limite superior (Upper Bound).

### Branch-and-Bound: 

Algoritmos exatos que exploram a árvore de busca para provar a solução ótima global.

Para otimizar o tempo de execução e a memória, o projeto conta com:

#### Máscaras de Bits:
Modelagem do universo e dos subconjuntos usando inteiros, permitindo operações de união e verificação em tempo $O(1)$.

#### Limitantes Inferiores (Lower Bounds): 
Uso das estratégias Packing e Sum-Degree para prever o custo futuro e realizar a poda prematura de subárvores.

#### Estratégias de Travessia: 
Implementação das abordagens de Busca em Profundidade (DFS) e Best-First (via Min-Heap).


## Saída

Os resultados são exportados automaticamente para a pasta OR_results em formato .csv.
O relatório gerado inclui para cada instância:

Status final (Optimal, Timeout, Out of Memory)

Custo ótimo encontrado

Tempo de processamento e consumo de Memória RAM (MB)

Quantidade de nós explorados e nós podados

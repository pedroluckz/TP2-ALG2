# Trabalho Prático II - Algoritmos II (DCC207)
Alice Lessa Ferreira <br>
Pedro Lucas Garcia Calais <br> <br>

# Problema de Cobertura de Conjuntos (Set Covering Problem)

Implementação e análise de desempenho de algoritmos aproximativos e exatos para a resolução da variante sem peso do Problema de Cobertura de Conjuntos (SCP).

## Como Executar

#### Para rodar o projeto, é necessário preparar as instâncias de teste:

Crie uma pasta chamada OR_instances no diretório raiz do projeto.

Baixe os arquivos de texto (.txt) das instâncias do SCP da OR-Library e coloque-os dentro dessa pasta.

Instâncias sintéticas (aleatórias e adversariais) foram criadas através do arquivo Instancegenerator.py e armazenadas na pasta testresults.

Para rodar o algoritmo aproximativo nas instâncias adversariais, execute:
```
python3 runadversarial.py
```

Para executar arquivo principal, que roda os algoritmos aproximativos e exatos para as instâncias aleatórias e reais,  via terminal:
```
python3 main.py
```

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

Nas instâncias sintéticas, é rodado o algoritmo aproximativo, assim como as 4 combinações de Lower Bounds e Estratégia de Travessia, e os resultados são salvos na pasta testresults. 

Já para as instâncias reais, são executados somente o algoritmo aproximativo e a combinação Sum-Degree + DFS de Branch and Bound, determinada como a melhor nos experimentos sintéticos. O resultado é salvo na pasta OR_results.


## Saída

#### O arquivo gerado inclui para cada instância:

Status final (Optimal, Timeout, Out of Memory)

Custo ótimo encontrado

Tempo de processamento e consumo de Memória RAM (MB)

Quantidade de nós explorados e nós podados

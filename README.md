# Rota Inteligente – Sabor Express

Projeto desenvolvido com foco em **Inteligência Artificial aplicada à logística de entregas**, utilizando **algoritmos de busca em grafos** e **clustering** para otimizar rotas, reduzir atrasos e diminuir custos operacionais.

---

##  Objetivo

Criar um sistema capaz de encontrar **rotas de entrega mais eficientes** em uma cidade representada como grafo, comparando diferentes algoritmos de busca e, em situações de alta demanda, organizando entregas em grupos por proximidade.

---

##  Problema

No cenário real de delivery, as rotas eram definidas manualmente, o que gerava:

- atrasos nas entregas;
- alto consumo de combustível;
- trajetos pouco eficientes;
- dificuldade de organização em horários de pico.

Para resolver isso, o projeto propõe uma abordagem baseada em algoritmos de Inteligência Artificial.

---

##  Solução Proposta

O sistema modela a cidade como um **grafo ponderado**, no qual:

- **nós (nodes)** representam bairros ou pontos de entrega;
- **arestas (edges)** representam ruas que conectam esses pontos;
- **pesos das arestas** representam o tempo estimado de deslocamento (`time_min`).

Com essa modelagem, é possível aplicar algoritmos clássicos de busca para encontrar rotas e comparar desempenho.

---

##  Algoritmos Utilizados

### 1. BFS — Breadth First Search
Busca em largura.

**Características:**
- explora os nós por níveis;
- não considera o peso das arestas;
- encontra o caminho com menor número de arestas, mas não necessariamente o mais rápido.

**Limitação:**
Em grafos com pesos diferentes, pode escolher uma rota pior em termos de tempo.

---

### 2. DFS — Depth First Search
Busca em profundidade.

**Características:**
- segue um caminho até o fim antes de voltar;
- pode encontrar uma solução rapidamente em alguns casos;
- não garante o melhor caminho.

**Limitação:**
Pode expandir caminhos ruins e gerar rotas ineficientes.

---

### 3. A* — Algoritmo principal
O algoritmo A* foi o principal método utilizado para otimização.

Sua função de avaliação é:

\[
f(n) = g(n) + h(n)
\]

Onde:

- **g(n)** = custo acumulado até o nó atual;
- **h(n)** = heurística, ou seja, estimativa do custo até o destino.

**Heurística utilizada:**
- distância estimada entre os pontos.

**Vantagens do A*:**
- considera custo real e estimativa futura;
- expande menos nós;
- encontra rotas mais eficientes;
- apresenta melhor equilíbrio entre desempenho e qualidade da solução.

> Observação: quando **h(n) = 0**, o A* se comporta como o algoritmo de **Dijkstra**.

---

### 4. K-Means (Clustering)
Aplicado em cenários com muitos pedidos.

**Regra de ativação do sistema:**
- se `pedidos >= 8`, o sistema ativa o **K-Means**.

**Função no projeto:**
- agrupar entregas próximas geograficamente em **clusters**;
- criar zonas de entrega;
- facilitar divisão entre entregadores.

**Benefícios:**
- redução de deslocamentos;
- melhor organização operacional;
- ganho de eficiência em horários de pico.

---

##  Modelagem do Problema

A cidade foi representada por um **grafo ponderado**, permitindo simular o ambiente urbano de forma computacional.

### Estrutura da modelagem

- **Nós (nodes):** bairros ou locais de entrega;
- **Arestas (edges):** conexões entre bairros;
- **Peso:** tempo estimado de deslocamento.

Essa representação permite comparar algoritmos de busca em um problema realista de logística.

---

##  Métricas Comparadas

O sistema compara os algoritmos com base em:

1. **tempo total da rota**;
2. **número de nós expandidos**;
3. **tempo de execução**.

Essas métricas são exibidas:

- na interface gráfica;
- no arquivo `report.txt`.

---

##  Interface Gráfica

O sistema possui uma interface desenvolvida em **Python Tkinter**, com:

- seleção de origem;
- seleção de destino;
- botão **Rodar Otimização**;
- tabela comparativa entre BFS, DFS e A*;
- log da execução;
- preview das imagens geradas.

---

##  Estrutura do Projeto

```bash
rota-inteligente-sabor-express
│
├─ src
│  ├─ gui.py
│  ├─ graph.py
│  ├─ search_algorithms.py
│  ├─ clustering.py
│  ├─ visualization.py
│  ├─ metrics.py
│
├─ data
│  ├─ nodes.csv
│  ├─ edges.csv
│  ├─ deliveries.csv
│
├─ outputs
│
├─ requirements.txt
└─ README.md


## Execução
```bash
pip install -r requirements.txt
python src/main.py

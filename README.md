# Rota Inteligente — Sabor Express

## Problema
A Sabor Express define rotas manualmente, causando atrasos e aumento de custos em horários de pico.

## Objetivo
- Modelar a cidade como grafo ponderado (tempo/distância)
- Encontrar menor caminho com A* e comparar com BFS/DFS
- Em pico, agrupar entregas por proximidade com K-Means

## Modelagem (Grafo)
- Nós: bairros
- Arestas: ruas com pesos (time_min, dist_km)

## Algoritmos
### BFS
Explora por níveis e encontra menor caminho em número de arestas (não considera peso).

### DFS
Explora em profundidade e não garante melhor caminho.

### A*
Busca informada usando:
f(n) = g(n) + h(n)
- g(n): custo acumulado (tempo)
- h(n): heurística (distância euclidiana)

### K-Means (Clustering)
Agrupa entregas por proximidade (lat/lon) para dividir “zonas” por entregador.

## Execução
```bash
pip install -r requirements.txt
python src/main.py

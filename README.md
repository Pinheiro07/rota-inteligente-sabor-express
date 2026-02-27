# Rota Inteligente — Otimização de Entregas com IA (Sabor Express)

## 1. Contexto e Problema
A empresa local de delivery “Sabor Express” enfrenta atrasos e aumento de custos por definir rotas manualmente, sem considerar distância/tempo e alta demanda em horários de pico.

## 2. Objetivo
Criar uma solução baseada em IA para:
- Representar a cidade como um grafo ponderado (distância/tempo);
- Encontrar menor caminho entre pontos de entrega com algoritmos de busca;
- Em alto volume, agrupar entregas próximas com clustering (K-Means);
- Comparar algoritmos e avaliar resultados com métricas.

## 3. Modelagem (Grafo)
- Nós: bairros/pontos de entrega (com latitude/longitude).
- Arestas: ruas (com pesos por distância e/ou tempo).
- O problema de roteamento é tratado como busca em grafo (menor caminho).

## 4. Algoritmos Utilizados
### 4.1 BFS (Busca em Largura)
- Encontra menor caminho em número de arestas, não considera pesos.
- Usado como baseline didático.

### 4.2 DFS (Busca em Profundidade)
- Explora caminhos profundamente, não garante melhor rota.
- Usado como comparação de eficiência/qualidade.

### 4.3 A* (A-estrela)
- Minimiza custo acumulado + heurística.
- Heurística: distância euclidiana entre coordenadas dos nós.
- Adequado para grafos ponderados com rotas urbanas.

### 4.4 K-Means (Clustering)
- Agrupa pedidos por proximidade geográfica (lat/lon).
- Em horários de pico, cada cluster vira “zona” de um entregador.
- Reduz distância total e evita cruzamento de rotas.

## 5. Como Executar
### 5.1 Instalar dependências
```bash
pip install -r requirements.txt

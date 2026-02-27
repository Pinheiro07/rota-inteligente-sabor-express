import os
import time
import pandas as pd

from graph import build_graph
from search_algorithms import bfs_path, dfs_path, astar_path
from clustering import kmeans_clusters
from metrics import path_cost
from visualization import draw_graph, draw_clusters, draw_route

PICO_MIN_PEDIDOS = 8
K_ENTREGADORES = 2

def main():
    os.makedirs("outputs", exist_ok=True)

    # 1) Carrega grafo
    G = build_graph("data/nodes.csv", "data/edges.csv")
    draw_graph(G, "outputs/graph.png")

    # 2) Carrega pedidos
    deliveries = pd.read_csv("data/deliveries.csv")
    n_pedidos = len(deliveries)

    # 3) Regra de pico
    if n_pedidos >= PICO_MIN_PEDIDOS:
        print(f"[PICO] {n_pedidos} pedidos >= {PICO_MIN_PEDIDOS} -> ativando K-Means (k={K_ENTREGADORES})")
        deliveries_clustered = kmeans_clusters(
            "data/deliveries.csv",
            k=K_ENTREGADORES,
            out_csv="outputs/deliveries_with_clusters.csv"
        )
        draw_clusters(deliveries_clustered, "outputs/clusters.png")
    else:
        print(f"[NORMAL] {n_pedidos} pedidos < {PICO_MIN_PEDIDOS} -> sem clustering (só rota)")
        # salva um arquivo “vazio” só pra ficar organizado
        deliveries.to_csv("outputs/deliveries_with_clusters.csv", index=False)

    # 4) Comparação de algoritmos (exemplo fixo)
    start = "Centro"
    goal = "Paraiso"

    # BFS
    t0 = time.time()
    p_bfs, ex_bfs = bfs_path(G, start, goal)
    ms_bfs = (time.time() - t0) * 1000
    cost_bfs = path_cost(G, p_bfs, "time_min") if p_bfs else None

    # DFS
    t0 = time.time()
    p_dfs, ex_dfs = dfs_path(G, start, goal)
    ms_dfs = (time.time() - t0) * 1000
    cost_dfs = path_cost(G, p_dfs, "time_min") if p_dfs else None

    # A*
    t0 = time.time()
    p_astar, ex_astar, cost_astar = astar_path(G, start, goal, weight="time_min")
    ms_astar = (time.time() - t0) * 1000

    # 5) Output visual da melhor rota (A*)
    draw_route(G, p_astar, "outputs/route_result.png")

    # 6) Relatório
    report = []
    report.append("RELATÓRIO - Sabor Express (Rota Inteligente)\n\n")
    report.append(f"Pedidos carregados: {n_pedidos}\n")
    report.append(f"Regra de pico: >= {PICO_MIN_PEDIDOS} pedidos ativa clustering\n\n")
    report.append(f"Exemplo de rota: {start} -> {goal}\n\n")
    report.append(f"BFS: caminho={p_bfs} | tempo_min={cost_bfs} | expandidos={ex_bfs} | ms={ms_bfs:.2f}\n")
    report.append(f"DFS: caminho={p_dfs} | tempo_min={cost_dfs} | expandidos={ex_dfs} | ms={ms_dfs:.2f}\n")
    report.append(f"A*:  caminho={p_astar} | tempo_min={cost_astar} | expandidos={ex_astar} | ms={ms_astar:.2f}\n")

    with open("outputs/report.txt", "w", encoding="utf-8") as f:
        f.writelines(report)

    print("OK! Gerado em outputs/: graph.png, clusters.png (se pico), route_result.png, report.txt")

if __name__ == "__main__":
    main()

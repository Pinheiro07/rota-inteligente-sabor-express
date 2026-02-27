import os
import matplotlib.pyplot as plt
import networkx as nx

def draw_graph(G, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.figure(figsize=(8, 6))
    pos = {n: G.nodes[n]["pos"] for n in G.nodes}
    nx.draw(G, pos, with_labels=True, node_size=900, font_size=8)
    plt.title("Grafo da cidade (bairros e ruas)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()

def draw_clusters(deliveries_df, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.figure(figsize=(7, 6))
    plt.scatter(deliveries_df["lon"], deliveries_df["lat"], c=deliveries_df["cluster"])
    plt.title("Clusters de entregas (K-Means)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()

def draw_route(G, path, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.figure(figsize=(8, 6))
    pos = {n: G.nodes[n]["pos"] for n in G.nodes}
    nx.draw(G, pos, with_labels=True, node_size=900, font_size=8, alpha=0.5)

    if path and len(path) >= 2:
        edges = list(zip(path[:-1], path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=edges, width=3)
        nx.draw_networkx_nodes(G, pos, nodelist=path, node_size=1100)

    plt.title("Rota destacada")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()

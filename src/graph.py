import pandas as pd
import networkx as nx

def build_graph(nodes_csv: str, edges_csv: str) -> nx.Graph:
    nodes = pd.read_csv(nodes_csv)
    edges = pd.read_csv(edges_csv)

    G = nx.Graph()

    for _, r in nodes.iterrows():
        G.add_node(
            r["node"],
            lat=float(r["lat"]),
            lon=float(r["lon"]),
            pos=(float(r["lon"]), float(r["lat"]))
        )

    for _, e in edges.iterrows():
        G.add_edge(
            e["u"], e["v"],
            dist_km=float(e["dist_km"]),
            time_min=float(e["time_min"])
        )

    return G

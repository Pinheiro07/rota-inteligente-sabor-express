def path_cost(G, path, weight="time_min"):
    if not path or len(path) < 2:
        return 0.0
    total = 0.0
    for i in range(len(path) - 1):
        total += float(G.edges[path[i], path[i+1]][weight])
    return total

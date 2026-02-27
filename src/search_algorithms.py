import math
import heapq

def bfs_path(G, start, goal):
    from collections import deque
    q = deque([start])
    parent = {start: None}
    visited = {start}
    expanded = 0

    while q:
        u = q.popleft()
        expanded += 1
        if u == goal:
            break
        for v in G.neighbors(u):
            if v not in visited:
                visited.add(v)
                parent[v] = u
                q.append(v)

    if goal not in parent:
        return None, expanded

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return list(reversed(path)), expanded

def dfs_path(G, start, goal):
    visited = set()
    parent = {start: None}
    expanded = 0
    found = False

    def rec(u):
        nonlocal expanded, found
        visited.add(u)
        expanded += 1
        if u == goal:
            found = True
            return
        for v in G.neighbors(u):
            if v not in visited and not found:
                parent[v] = u
                rec(v)

    rec(start)

    if not found:
        return None, expanded

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return list(reversed(path)), expanded

def _euclid_latlon(G, a, b):
    la1, lo1 = G.nodes[a]["lat"], G.nodes[a]["lon"]
    la2, lo2 = G.nodes[b]["lat"], G.nodes[b]["lon"]
    return math.sqrt((la1-la2)**2 + (lo1-lo2)**2)

def astar_path(G, start, goal, weight="time_min"):
    # heurística admissível "didática": distância euclidiana (escalada)
    def h(n):
        return _euclid_latlon(G, n, goal) * 1000

    open_heap = [(h(start), start)]
    g = {start: 0.0}
    parent = {start: None}
    closed = set()
    expanded = 0

    while open_heap:
        _, u = heapq.heappop(open_heap)
        if u in closed:
            continue
        expanded += 1

        if u == goal:
            break

        closed.add(u)

        for v in G.neighbors(u):
            w = float(G.edges[u, v][weight])
            tentative = g[u] + w
            if v not in g or tentative < g[v]:
                g[v] = tentative
                parent[v] = u
                heapq.heappush(open_heap, (tentative + h(v), v))

    if goal not in parent:
        return None, expanded, None

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path, expanded, g[goal]

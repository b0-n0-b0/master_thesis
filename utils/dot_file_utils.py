import pydot
from collections import defaultdict

def load_dot_file(path):
    graphs = pydot.graph_from_dot_file(path)
    return graphs[0] if graphs else None

def normalize_node(name):
    return name.strip('"')

def build_adjacency_and_reverse(graph):
    adj = defaultdict(list)
    rev_adj = defaultdict(list)
    for edge in graph.get_edges():
        src = normalize_node(edge.get_source())
        dst = normalize_node(edge.get_destination())
        adj[src].append(dst)
        rev_adj[dst].append(src)
    return adj, rev_adj

def find_all_paths_to_target(adj, roots, target):
    paths = []
    visited = set()
    success_cache = defaultdict(set)
    fail_cache = set()
    def dfs(node, path):
        if node == target:
            paths.append(path[:])
            return True, [node]

        # Memoization
        if node in fail_cache:
            # print(f"fail hit at node {node}")
            return False, None
        
        if node in success_cache and success_cache[node]:
            # print(f"cache hit from {node}")
            for cached_path in success_cache[node]:  # cached_path is a tuple
                paths.append(path[:] + list(cached_path)[1:])
            return True, list(cached_path) 

        found_path = False
        to_cache_path = None
        for child in adj.get(node, []):
            if child in path:
                continue  # Avoid cycles
            path.append(child)
            found_path, to_cache_path = dfs(child, path)
            path.pop()

            if found_path:
                # must be an array
                to_cache_path.insert(0,node)
#                 print(f"__________")
                # print(f"to_cache_path -> {to_cache_path}")
                success_cache[node].add(tuple(to_cache_path))
                # print(f"from {node} caching {success_cache[node]}")
                # print(f"value inserted in success_cache[{node}]")
                # print(f"__________")
        if not found_path:
            fail_cache.add(node)
        return found_path, to_cache_path

    for root in roots:
        if root in visited:
            continue
        dfs(root, [root])
    return paths

def build_subgraph_from_paths(paths, exported_nodes):
    new_graph = pydot.Dot(graph_type='digraph')
    nodes = set()
    edges = set()

    for path in paths:
        for i in range(len(path)):
            nodes.add(path[i])
            if i > 0:
                edges.add((path[i - 1], path[i]))

    for node in nodes:
        dot_node = pydot.Node(node)
        if node in exported_nodes:
            dot_node.set_comment("exported")
        new_graph.add_node(dot_node)

    for src, dst in edges:
        new_graph.add_edge(pydot.Edge(src, dst))

    return new_graph

def build_target_subgraph(graph, target_node, exported_nodes):
    adj, _ = build_adjacency_and_reverse(graph)
    target_node = normalize_node(target_node)
    exported_nodes = [normalize_node(n) for n in exported_nodes]

    paths = find_all_paths_to_target(adj, exported_nodes, target_node)

    if paths:
        return build_subgraph_from_paths(paths, exported_nodes)
    else:
        return None

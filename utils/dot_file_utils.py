import pydot

def load_dot_file(path):
    graphs = pydot.graph_from_dot_file(path)
    return graphs[0] if graphs else None

def build_adjacency_and_reverse(graph):
    adj = {}
    rev_adj = {}
    for edge in graph.get_edges():
        src = edge.get_source().strip('"')
        dst = edge.get_destination().strip('"')
        adj.setdefault(src, []).append(dst)
        rev_adj.setdefault(dst, []).append(src)
    return adj, rev_adj

def find_roots(adj, rev_adj):
    all_nodes = set(adj.keys()) | {n for dests in adj.values() for n in dests}
    non_roots = set(rev_adj.keys())
    return list(all_nodes - non_roots)

def find_all_paths_to_target(adj, roots, target):
    paths = []

    def dfs(node, path):
        if node == target:
            paths.append(path[:])
            return
        for child in adj.get(node, []):
            if child not in path:  # avoid cycles
                path.append(child)
                dfs(child, path)
                path.pop()

    for root in roots:
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
    adj, rev_adj = build_adjacency_and_reverse(graph)
    roots = find_roots(adj, rev_adj)
    paths = find_all_paths_to_target(adj, roots, target_node)
    
    if paths:
        subgraph = build_subgraph_from_paths(paths, exported_nodes)
        return subgraph
    else:
        return None

# if __name__ == "__main__":
#     dot_file = "test.dot"
#     target_node = "node0"
    
#     graph = load_dot_file(dot_file)
#     build_target_subgraph(graph, target_node)

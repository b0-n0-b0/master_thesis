import argparse
import os
from multiprocessing import Pool, cpu_count
from utils.rule_parser_lark import parse_rule_file
from utils.collections_utils import generate_ordered_valid_combinations, is_valid_rule_match_sequence
from utils.wassail_utils import get_rule_matches, get_exported_nodes, get_cfg
from utils.dot_file_utils import build_target_subgraph
from solver import run_symbolic_execution, InstructionHookPlugin, CallHookPlugin

def symbolic_exec_task(args):
    """Wrapper for parallel symbolic execution with InstructionHookPlugin"""
    module, fidx, valid_match_sequence = args
    for match in valid_match_sequence:
        print(f"________________________\nSymbolic execution of function {fidx} with target:\n{match}\n\n________________________", flush=True)
    constraints = run_symbolic_execution(module, fidx, InstructionHookPlugin(valid_match_sequence))
    return (fidx, constraints)

def edge_exec_task(args):
    """Wrapper for parallel symbolic execution for control flow edges"""
    module, src_function, dst_function = args
    constraints = run_symbolic_execution(module, src_function, CallHookPlugin(dst_function))
    return (src_function, dst_function, constraints)

def main():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("rules", help="Path of the file containing the rules")
    parser.add_argument("module", help="Path of the file containing the WASM module to analyze")
    args = parser.parse_args()

    rule_set = parse_rule_file(args.rules)
    rule_matches = get_rule_matches(rule_set, args.module)

    if len(rule_matches) == 0:
        print("No match for the provided rule was found...", flush=True)
        return

    key_order = rule_set.application_order
    cfg = get_cfg(args.module)
    found_constraints = {}

    # Step 1: Prepare tasks for symbolic execution of rule matches
    symbolic_tasks = []
    for combo in generate_ordered_valid_combinations(rule_matches, is_valid_rule_match_sequence, key_order):
        valid_match_sequence = list(combo.values()) # contains a sequence of matches that respects the order enforced by the rule file
        for rule_match in valid_match_sequence:
            symbolic_tasks.append((args.module, rule_match.fidx, valid_match_sequence))

    # Step 2: Run symbolic executions in parallel
    with Pool(processes=min(cpu_count()//3, len(symbolic_tasks))) as pool:
        symbolic_results = pool.map(symbolic_exec_task, symbolic_tasks)

    # Step 3: Collect results
    for fidx, constraints in symbolic_results:
        if constraints:
            print(f"Constraints for function {fidx}:", flush=True)
            for c in constraints:
                print(c, flush=True)
            found_constraints.setdefault(fidx, []).append(constraints)

    # TODO: optimize by removing the repetition of the subgraph generation
    # Step 4: Build subgraphs and prepare edge execution tasks
    exported_nodes = get_exported_nodes(args.module)
    edge_tasks = []
    sub_callgraph_list = []
    for fidx, _ in found_constraints.items():
        sub_callgraph = build_target_subgraph(cfg, f"node{fidx}", exported_nodes)
        edges = sub_callgraph.get_edges()
        for edge in edges:
            src_function = int(edge.get_source().strip('"').strip("node"))
            dst_function = int(edge.get_destination().strip('"').strip("node"))
            edge_tasks.append((args.module, src_function, dst_function))
        sub_callgraph_list.append(sub_callgraph)

    # Step 5: Run edge-based symbolic executions in parallel
    with Pool(processes=min(cpu_count(), len(edge_tasks))) as pool:
        edge_results = pool.map(edge_exec_task, edge_tasks)

    # # Step 6: Annotate the CFG with constraints
    edge_constraints_map = {(src, dst): cons for src, dst, cons in edge_results}
    for sub_callgraph in sub_callgraph_list:
        edges = sub_callgraph.get_edges()
        for edge in edges:
            src_function = int(edge.get_source().strip('"').strip("node"))
            dst_function = int(edge.get_destination().strip('"').strip("node"))
            edge.set_comment(edge_constraints_map.get((src_function, dst_function), []))
        for edge in edges:
            print(f"In order to go from function {edge.get_source().strip('node')} to function {edge.get_destination().strip('node')} the constraints are:", flush=True)
            for idx, c in enumerate(edge.get_comment()):
                print(f"_______________constraint set {idx+1}_______________", flush=True)
                print(c, flush=True)
        print(sub_callgraph)

if __name__ == "__main__":
    main()

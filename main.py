import argparse
import os
import logging
import sys
from multiprocessing import Pool, cpu_count, Manager
from utils.rule_parser_lark import parse_rule_file
from utils.collections_utils import generate_ordered_valid_combinations, is_valid_rule_match_sequence
from utils.wassail_utils import get_rule_matches, get_exported_nodes, get_callgraph
from utils.dot_file_utils import build_target_subgraph
from solver import run_symbolic_execution, InstructionHookPlugin, CallHookPlugin

def setup_logging(debug: bool, logfile: str = "app.log"):
    # Console handler (goes to Docker logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)

    # File handler
    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)

    # Common formatter
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        handlers=[console_handler, file_handler],
        force=True,
    )

def symbolic_exec_task(args):
    """Wrapper for parallel symbolic execution with InstructionHookPlugin"""
    module, fidx, valid_match_sequence = args
    logging.debug(f"________________________\nSymbolic execution of function {fidx} with match sequence:")
    for match in valid_match_sequence:
        logging.debug(f"\n{match}\n")
    logging.debug("________________________")

    try:
        constraints = run_symbolic_execution(module, fidx, InstructionHookPlugin(valid_match_sequence))
        return (fidx, constraints)
    except Exception as e:
        logging.error(e)
        return None

def edge_exec_task(args):
    """Wrapper for parallel symbolic execution for control flow edges"""
    module, src_function, dst_function, found_edge_constraints = args
    if (src_function,dst_function) in found_edge_constraints:
        return (src_function, dst_function, found_edge_constraints[(src_function,dst_function)])
    logging.debug(f"calculating {src_function} -> {dst_function}")
    constraints = run_symbolic_execution(module, src_function, CallHookPlugin(dst_function, src_function))
    found_edge_constraints[(src_function,dst_function)] = constraints
    return (src_function, dst_function, constraints)

def main():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("rules", help="Path of the file containing the rules")
    parser.add_argument("module", help="Path of the file containing the WASM module to analyze")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "-j","--jobs",
        type=int,
        default=4,
        help="Number of concurrent processes to use for parallel execution (default: 4)"
    )
    args = parser.parse_args()
    setup_logging(args.debug)

    args.jobs = min(cpu_count(), args.jobs)

    rule_set = parse_rule_file(args.rules)
    rule_matches = get_rule_matches(rule_set, args.module)

    if len(rule_matches) == 0:
        logging.info("No match for the provided rule set was found")
        return
    #NOTE: test for /inputs/1318-axosnake.wasm
    # rule_matches[0] = rule_matches[0][58:59]
    key_order = rule_set.application_order
    callgraph = get_callgraph(args.module)
    found_constraints = {}

    # Step 1: Prepare tasks for symbolic execution of rule matches
    symbolic_tasks = []
    for combo in generate_ordered_valid_combinations(rule_matches, is_valid_rule_match_sequence, key_order):
        valid_match_sequence = list(combo.values()) # contains a sequence of matches that respects the order enforced by the rule file
        symbolic_tasks.append((args.module, valid_match_sequence[0].fidx, valid_match_sequence))
    
    # NOTE: it was impossible to build a match sequence that satisfies the expected rule sequence 
    if len(symbolic_tasks) == 0:
        logging.info("No match for the provided rule set was found")
        return

    # Step 2: Run symbolic executions in parallel
    with Pool(processes=args.jobs) as pool:
        symbolic_results = pool.map(symbolic_exec_task, symbolic_tasks)
    symbolic_results = [sym_res for sym_res in symbolic_results if sym_res is not None]

    # Step 3: Collect results
    for fidx, constraints in symbolic_results:
        if constraints:
            logging.debug(f"Constraints for function {fidx}:")
            for c in constraints:
                logging.debug(c)
            found_constraints.setdefault(fidx, []).append(constraints)

    # Step 4: Build subgraphs and prepare edge execution tasks
    exported_nodes = get_exported_nodes(args.module)
    edge_tasks = []
    sub_callgraph_list = []
    # NOTE: create a shared dict containing tuples ((src,dst), constraints)
    manager = Manager()
    found_edge_constraints = manager.dict()
    # NOTE: create the tasks to edge tasks to be executed in parallel
    for fidx, _ in found_constraints.items():
        sub_callgraph = build_target_subgraph(callgraph, f"node{fidx}", exported_nodes)
        edges = sub_callgraph.get_edges()
        for edge in edges:
            src_function = int(edge.get_source().strip('"').strip("node"))
            dst_function = int(edge.get_destination().strip('"').strip("node"))
            edge_tasks.append((args.module, src_function, dst_function, found_edge_constraints))
        sub_callgraph_list.append(sub_callgraph)
        logging.debug(f"sub-callgraph for function {fidx}:")
        logging.debug(sub_callgraph)
    
    # Step 5: Run edge-based symbolic executions in parallel
    with Pool(processes=args.jobs) as pool:
        edge_results = pool.map(edge_exec_task, edge_tasks)

    # Step 6: Annotate the callgraph with constraints
    edge_constraints_map = {(src, dst): cons for src, dst, cons in edge_results}
    for sub_callgraph in sub_callgraph_list:
        edges = sub_callgraph.get_edges()
        for edge in edges:
            src_function = int(edge.get_source().strip('"').strip("node"))
            dst_function = int(edge.get_destination().strip('"').strip("node"))
            edge.set_comment(edge_constraints_map.get((src_function, dst_function), []))
        # for edge in edges:
        #     print(f"In order to go from function {edge.get_source().strip('node')} to function {edge.get_destination().strip('node')} the constraints are:", flush=True)
        #     for idx, c in enumerate(edge.get_comment()):
        #         print(f"_______________constraint set {idx+1}_______________", flush=True)
        #         print(c, flush=True)
        print(sub_callgraph)

# TODO: add constraints to the target function in the output DOT file

if __name__ == "__main__":
    main()

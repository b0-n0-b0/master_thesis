import argparse
import subprocess
import os 
from utils.rule_parser_lark import parse_rule_file
from utils.collections_utils import generate_ordered_valid_combinations, is_valid_rule_match_sequence
from utils.wassail_utils import get_rule_matches, get_exported_nodes, get_cfg
from utils.dot_file_utils import load_dot_file, build_target_subgraph
from solver import run_symbolic_execution, InstructionHookPlugin, CallHookPlugin

def main():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("rules", help="Path of the file containing the rules")
    parser.add_argument("module", help="Path of the file containing the WASM module to analyze")

    args = parser.parse_args()
    rule_set = parse_rule_file(args.rules)
    rule_matches = get_rule_matches(rule_set, args.module)
    if len(rule_matches) == 0:
        print("No match for the provided rule was found, please check the rule file, the wasm module input and the wassail compatibility", flush=True)
        return
    # NOTE: generate all valid combinations and run the symbolic execution for each of those
    key_order = rule_set.application_order
    # NOTE: generate CFG
    cfg = get_cfg(args.module)
    for combo in generate_ordered_valid_combinations(rule_matches, is_valid_rule_match_sequence, key_order):
        rule_match_list = []
        for value in combo.values():
            rule_match_list.append(value)
        for rule_match in rule_match_list:
            current_fidx = rule_match.fidx
            print(f"Symbolic execution of function {current_fidx} with target:\n{rule_match}\n", flush=True)
            constraints = run_symbolic_execution(args.module, current_fidx, InstructionHookPlugin(rule_match_list))
            if len(constraints) == 0:
                continue
            print(f"Constraints to match the applied rules:", flush=True)
            print(f"_______________constraints for function {current_fidx}_______________\n", flush=True)
            for c in constraints:
                print(c, flush=True)
            
            exported_nodes = get_exported_nodes(args.module)
            print("before build subcfg", flush=True)
            sub_cfg = build_target_subgraph(cfg, f"node{current_fidx}", exported_nodes)
            print("after build subcfg", flush=True)
            edges = sub_cfg.get_edges()
            print(f"the subtree for function {current_fidx} has {len(edges)} edges", flush=True)
            for edge in edges:
                src_function = int(edge.get_source().strip('"').strip("node"))
                dst_function = int(edge.get_destination().strip('"').strip("node"))
                print(f"running symbolic execution in order to get from {src_function} to {dst_function}", flush=True)
                constraints = run_symbolic_execution(args.module, src_function, CallHookPlugin(dst_function))
                edge.set_comment(constraints)
            for edge in edges:
                print(f"In order to go from function {edge.get_source().strip('node')} to function {edge.get_destination().strip('node')} the constraints are:", flush=True)
                for idx, c in enumerate(edge.get_comment()):
                    print(f"_______________constraint set {idx+1}_______________", flush=True)
                    print(c, flush=True)
            print(sub_cfg)
    # sub_cfg.write_raw('output.dot')
if __name__ == "__main__":
    main()
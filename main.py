import argparse
import subprocess
import os 
from utils.rule_parser_lark import parse_rule_file
from utils.collections_utils import generate_ordered_valid_combinations, is_valid_rule_match_sequence
from utils.wassail_parse import parse_wassail_output
from utils.dot_file_utils import load_dot_file, build_target_subgraph
from solver import run_symbolic_execution_instruction_plugin, run_symbolic_execution_call_plugin

def main():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("rules", help="Path of the file containing the rules")
    parser.add_argument("module", help="Path of the file containing the WASM module to analyze")

    args = parser.parse_args()
    rule_set = parse_rule_file(args.rules)
    target_instructions = []
    # NOTE: generate input for wassail
    wassail_input = ""
    for rule in rule_set.rules:
        wassail_input = wassail_input +  rule.target_instruction + ","
    wassail_input = wassail_input[:-1]
    # TODO: remove path and set $PATH before
    result = subprocess.run(["/home/b0n0b0/thesis/wassail-master_thesis/_build/install/default/bin/wassail","apply-rule",args.module ,wassail_input], capture_output=True)
    # NOTE: parse found matches from wassail
    rule_matches = parse_wassail_output(result, rule_set)
    # NOTE: generate all valid combinations and run the symbolic execution for each of those
    key_order = rule_set.application_order
    # NOTE: generate CFG
    subprocess.run(["/home/b0n0b0/thesis/wassail-master_thesis/_build/install/default/bin/wassail","callgraph",args.module, "cfg.dot"], capture_output=True)
    cfg = load_dot_file("cfg.dot")
    for combo in generate_ordered_valid_combinations(rule_matches, is_valid_rule_match_sequence, key_order):
        rule_match_list = []
        for value in combo.values():
            rule_match_list.append(value)
        # for match in rule_match_list:
        #     print(match)
        # print(f"Symbolic execution of function {rule_match_list[0].fidx}")
        constraints = run_symbolic_execution_instruction_plugin(args.module, rule_match_list,rule_match_list[0].fidx)
        print(f"Constraints to match the applied rules:")
        print(f"_______________constraints for function {rule_match_list[0].fidx}_______________\n")
        for c in constraints:
            print(c)
        
        # TODO: once found the constraints for each potential combination traverse the CFG in order to create an annotated CFG 
        sub_cfg = build_target_subgraph(cfg, f"node{rule_match_list[0].fidx}")
        edges = sub_cfg.get_edges()
        for edge in edges:
            constraints = run_symbolic_execution_call_plugin(args.module,int(edge.get_source().strip('"').strip("node")), rule_match_list[0].fidx)
            edge.set_comment(constraints)
        for edge in edges:
            print(f"In order to go from function {edge.get_source().strip('node')} to function {edge.get_destination().strip('node')} the constraints are:")
            for idx, c in enumerate(edge.get_comment()):
                print(f"_______________constraint set {idx+1}_______________")
                print(c)
if __name__ == "__main__":
    main()
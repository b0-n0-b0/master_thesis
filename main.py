import argparse
import subprocess
import os 
from utils.rule_parser_lark import parse_rule_file
from utils.collections_utils import generate_ordered_valid_combinations, is_valid_rule_match_sequence
from utils.wassail_parse import parse_wassail_output
from solver import run_symbolic_execution

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
    for combo in generate_ordered_valid_combinations(rule_matches, is_valid_rule_match_sequence, key_order):
        rule_match_list = []
        for value in combo.values():
            rule_match_list.append(value)
        print(f"Symbolic execution of function {rule_match_list[0].fidx}")
        run_symbolic_execution(args.module, rule_match_list,rule_match_list[0].fidx)

    # TODO: with the wassail output + rule set, call manticore
    
if __name__ == "__main__":
    main()
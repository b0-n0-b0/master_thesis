from utils.rule_parser import RuleSet, RuleMatch
import argparse
import subprocess
import os 
from collections import defaultdict
from itertools import product
from solver import run_symbolic_execution

# generate all the valid combinations for a sequence of rules
def generate_ordered_valid_combinations(data_map, check_function, key_order):
    keys = list(data_map.keys())
    value_lists = [data_map[key] for key in keys]

    for values in product(*value_lists):
        combo = dict(zip(keys, values))
        ordered = reorder_combination(combo, key_order)
        if check_function(ordered):
            yield ordered
# valid sequence check
def is_valid_match_sequence(combination):
    last_fidx = None
    last_offset = None
    for rule_match in combination.values():
        # instructions must be part of the same function
        if last_fidx == None:
            last_fidx = rule_match.fidx
        elif last_fidx != rule_match.fidx:
            return False
        # instruction in the same function must be in sequence
        if last_offset == None:
            last_offset = rule_match.offset
        elif last_offset >= rule_match.offset:
            return False
    return True
# Reorder combination
def reorder_combination(combo, key_order):
    return {key: combo[key] for key in key_order if key in combo}

def main():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("rules", help="Path of the file containing the rules")
    parser.add_argument("module", help="Path of the file containing the WASM module to analyze")

    args = parser.parse_args()
    rule_set = RuleSet(args.rules)
    target_instructions = []
    # NOTE: generate input for wassail
    wassail_input = ""
    for rule in rule_set.rules:
        wassail_input = wassail_input +  rule.target_instruction + ","
    wassail_input = wassail_input[:-1]
    # TODO: remove path and set $PATH before
    result = subprocess.run(["/home/b0n0b0/thesis/wassail-master_thesis/_build/install/default/bin/wassail",f"apply-rule",args.module ,wassail_input], capture_output=True)
    # NOTE: parse found matches from wassail
    matches = result.stdout.decode('utf-8').strip().split("\n")
    rule_matches = defaultdict(list)
    for match in matches:
        rule_id, info = match.split("|")
        rule_id = int(rule_id)
        fidx, offset = info.split(",")
        fidx = int(fidx)
        offset = int(offset)
        rule_matches[rule_id].append(RuleMatch(rule_set.rules[rule_id], fidx, offset))
    
    #NOTE: generate all valid combinations
    key_order = rule_set.application_order
    for combo in generate_ordered_valid_combinations(rule_matches, is_valid_match_sequence, key_order):
        rule_match_list = []
        for value in combo.values():
            rule_match_list.append(value)
        print(f"Symbolic execution of function {rule_match_list[0].fidx}")
        run_symbolic_execution(args.module, rule_match_list,rule_match_list[0].fidx)

    # TODO: with the wassail output + rule set, call manticore
    
if __name__ == "__main__":
    main()
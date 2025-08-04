from utils.rule_parser_lark import RuleMatch
from utils.dot_file_utils import load_dot_file
from collections import defaultdict
import subprocess

def parse_wassail_output(output, rule_set):
    matches = output.stdout.decode('utf-8').strip().split("\n")
    rule_matches = defaultdict(list)
    for match in matches:
        if len(match) > 1:
            rule_id, info = match.split("|")
            fidx, offset = info.split(",")

            rule_id = int(rule_id)
            fidx = int(fidx)
            offset = int(offset)

            matched_rule = rule_set.rules[rule_id] 
            rule_matches[rule_id].append(RuleMatch(matched_rule, fidx, offset))
    return rule_matches
    
def get_rule_matches(rule_set, module):
    wassail_input = ""
    for rule in rule_set.rules:
        wassail_input = wassail_input +  rule.target_instruction + ","
    wassail_input = wassail_input[:-1]
    output = subprocess.run(["wassail","apply-rule", module ,wassail_input], capture_output=True)
    if len(output.stderr) > 0:
        print(f"[WARNING]: unexpected output from wassail:\n{output.stderr.decode('utf-8')}", flush=True)
    # NOTE: parse found matches from wassail
    rule_matches = parse_wassail_output(output, rule_set)
    return rule_matches

def get_exported_nodes(module):
    output = subprocess.run(["wassail","exports",module], capture_output=True)
    if len(output.stderr) > 0:
        print(f"[WARNING]: unexpected output from wassail:\n{output.stderr.decode('utf-8')}", flush=True)
    exported_nodes = []
    for line in output.stdout.decode('utf-8').split("\n")[:-1]:
        exported_nodes.append("node"+line.split("\t")[0])
    return exported_nodes

def get_cfg(module):
    output = subprocess.run(["wassail","callgraph", module, "callgraph.dot"], capture_output=True)
    if len(output.stderr) > 0:
        print(f"[WARNING]: unexpected output from wassail:\n{output.stderr.decode('utf-8')}", flush=True)
    cfg = load_dot_file("callgraph.dot")
    return cfg
from utils.rule_parser_lark import RuleMatch
from collections import defaultdict

def parse_wassail_output(output, rule_set):
    matches = output.stdout.decode('utf-8').strip().split("\n")
    rule_matches = defaultdict(list)
    for match in matches:
        rule_id, info = match.split("|")
        fidx, offset = info.split(",")

        rule_id = int(rule_id)
        fidx = int(fidx)
        offset = int(offset)

        matched_rule = rule_set.rules[rule_id] 
        rule_matches[rule_id].append(RuleMatch(matched_rule, fidx, offset))
    return rule_matches
    
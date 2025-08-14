from collections import defaultdict
from itertools import product

# generate all the valid combinations for a sequence of rules
def generate_ordered_valid_combinations(data_map, check_function, key_order):
    keys = list(data_map.keys())
    # NOTE: create combinations only if there is at least one match per rule
    unique_keys = list(dict.fromkeys(keys))
    if set(unique_keys) != set(key_order):
        return None
    
    value_lists = [data_map[key] for key in keys]
    for values in product(*value_lists):
        combo = dict(zip(keys, values))
        ordered = reorder_combination(combo, key_order)

        if check_function(ordered):
            yield ordered
# valid sequence check
def is_valid_rule_match_sequence(combination):
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
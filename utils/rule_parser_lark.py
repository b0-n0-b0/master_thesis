from lark import Lark, Transformer, v_args
import os
# Reusing your grammar
file_path = os.path.join(os.path.dirname(__file__), 'rule_grammar.lark')
rule_grammar = open(file_path).read()

# Model classes
class RuleMatch():
    def __init__(self, rule, fidx, offset):
        self.rule = rule
        self.fidx = fidx
        self.offset = offset
        self.symbolic_parameters = []
    def __str__(self):
        return f"______ {self.rule.name} ______\nfunction: {self.fidx}\noffset: {self.offset}\ninstruction:{self.rule.target_instruction}"

class Rule():
    def __init__(self, name, target_instruction, parameters=None, constraints=None):
        self.name = name
        self.target_instruction = target_instruction
        self.parameters = parameters or []
        self.constraints = constraints or []
    def __str__(self):
        return f"______ {self.name} ______\ntarget instruction: {self.target_instruction}\nparameters: {self.parameters}\nconstraints: {self.constraints}"

class RuleSet():
    def __init__(self, rules, sequence):
        self.rules = rules
        self.sequence = sequence
        self.application_order = []

        for seq_name in self.sequence:
            matched = next((i for i, rule in enumerate(self.rules) if rule.name == seq_name), None)
            if matched is None:
                raise Exception(f"Invalid rule name in sequence: {seq_name}")
            self.application_order.append(matched)

    def __str__(self):
        output  = "------ RULES ------\n\n"
        for rule in self.rules:
            output += str(rule) + "\n"
        output += "\n------ RULES SEQUENCE ------\n\n"
        output += " > ".join(self.sequence)
        return output

# Lark Transformer to convert tree to Rule/RuleSet
class RuleTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.rules = []
        self.sequence = []

    def rule_line(self, items):
        name = str(items[0])
        mnemonic = str(items[1])
        params = items[2]  # Already a list of strings
        constraints = items[3]  # Already a list of strings
        self.rules.append(Rule(name, mnemonic, params, constraints))

    def rule_sequence_line(self, items):
        self.sequence = [str(item).replace(" ", "") for item in items]

    def param_name(self, items):
        return str(items[0]).replace(" ","")  # Token

    def param_condition(self, items):
        return str(items[0]).replace(" ","")  # Token

    def param_name_list(self, items):
        return items  # already converted by param_name

    def param_condition_list(self, items):
        return items  # already converted by param_condition

    def start(self, _):
        return RuleSet(self.rules, self.sequence)

# Parser setup
rule_parser = Lark(rule_grammar, parser="lalr", lexer="contextual", transformer=RuleTransformer())

# Example of use
def parse_rule_file(path):
    with open(path, 'r') as file:
        content = file.read()
        ruleset = rule_parser.parse(content)
        return ruleset

if __name__ == "__main__":
    ruleset = parse_rule_file("../test.rule")
    print(ruleset)

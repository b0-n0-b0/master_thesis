import re
class Rule():
    def __init__(self, name, target_instruction, parameters, constraints=[]):
        self.name = name
        # mnemonic target
        self.target_instruction = target_instruction
        # list of target's instruction parameters (with names) 
        self.parameters = parameters
        # list of constraints to apply
        self.constraints = constraints
    def __str__(self):
        return f"______ {self.name} ______\ntarget instruction: {self.target_instruction}\nparameters: {self.parameters}\nconstraints: {self.constraints}"

class RuleSet():
    rules = []
    sequence  = []
    def __init__(self, rule_file):
        with open(rule_file, 'r') as file:
            for line in file:
                # remove comments
                clean_line = line.replace(" ", "").strip().split("#")[0]
                # parsing the rule sequence statement
                if clean_line[0] == "!":
                    rule_sequence = clean_line.split("!")[1].split(">")
                    self.sequence = rule_sequence
                    break
                # parsing a rule statement
                else:
                    rule_name, rule = clean_line.split("|")
                    # parse actual Rule object:
                    target, constraints = rule.split(";")
                    constraints = constraints.split(",")
                    target_instruction, params = target.split(":")
                    params=params.split(',')
                    # check on param name correctness
                    for param in params:
                        assert(re.match("^[a-zA-Z][a-z,A-Z,0-9,_]*$", param))
                    self.rules.append(Rule(rule_name, target_instruction, params, constraints))
        print(self)

    def __str__(self):
        output  = "------ rules ------\n"
        for rule in self.rules:
            output = output + rule.__str__() + "\n"
        output = output + "------ Rule sequence ------\n"
        for seq_elem in self.sequence:
            output = output + seq_elem +" "
        return output

if __name__ == "__main__":
    rule_set = RuleSet("./rule.set")
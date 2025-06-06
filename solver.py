from manticore.wasm import ManticoreWASM, types
from manticore.core.plugin import Plugin
from utils.rule_parser import RuleInstance, Rule

class Param():
    def __init__(self, name, size):
        self.name = name
        self.size = size

class InstructionHookPlugin(Plugin):
    """A plugin that hooks instruction execution and applies constraints"""

    def __init__(self, rule_instances):
        super().__init__()
        # solve for the input symbols once these are over
        self.rule_instances = rule_instances
        self.current_rule_idx = 0

    def generic_solver(self, state, current_instruction):
        if len(self.rule_instances) > 0:
            current_rule = self.rule_instances[self.current_rule_idx]
            # we reverse the array because WASM is a stack machine (last pushed value is the last param of the instruction)
            # match target instruction
            if current_instruction.funcaddr == current_rule.fidx and current_instruction.offset == current_rule.offset:
                # we found the rule match, we can proceed to the next one
                symbolic_parameters = []
                # create parameters starting from the rule
                for idx, param in enumerate(current_rule.rule.parameters[::-1]):
                    symbolic_parameters.append(state.stack.peek_nth(idx+1)) 
                current_rule.symbolic_parameters = symbolic_parameters
                # NOTE: moving the constraint evaluation to the end allows for more complex constraints; we can i.e. enforce 
                # constraints that involve parameters of different instructions
                # we've met all the rules, now we apply all the constraints and solve for the function params
                if self.current_rule_idx == len(self.rule_instances)-1:
                    # define all the parameters
                    for rule_instance in self.rule_instances:
                        for idx, parameter in enumerate(rule_instance.rule.parameters):
                            locals()[parameter] = rule_instance.symbolic_parameters[idx] 
                    # apply all the constraints
                    for rule_instance in self.rule_instances:
                         for constraint in rule_instance.rule.constraints:
                            state.constrain(eval(constraint))
                    # solve
                    for sym in state.input_symbols:
                        solved = state.solve_n(sym,1)
                        print(f"solution for {sym.name}: {solved}")
                self.current_rule_idx += 1

    def will_execute_instruction_callback(self, state, *args):
        # self.example_solver_for_add_if(state, *args)
        instruction = args[0]
        self.generic_solver(state, instruction)
        # print(f"In function: {instruction.funcaddr} executing {instruction.mnemonic} @ offset {instruction.offset}")
    def will_call_function_callback(self, state, *args):
        called_function = args[0]
        print(f"will call function {called_function}")



# in order to invoke a wasm fuction with symbolic parameters, 
# we use a function that returns an array of symbolic values 
# with types compatibles with the function signature
def param_generator(state, params):
    sym_params = []
    for param in params:
        sym_params.append(state.new_symbolic_value(param.size, param.name))
    return sym_params

# Initialize ManticoreWASM with the target WebAssembly file
m = ManticoreWASM("../tests/hello_world/hello_world.wasm")
# Register our instruction execution hook
# The Rule is provided by the RuleSet, fidx and offset are provided by the wassail output 
m.register_plugin(InstructionHookPlugin([
    RuleInstance(Rule("name","i32.add",["arg1", "arg2"],[]),fidx=2, offset=2),
    RuleInstance(Rule("name","i32.add",["arg3", "arg4"],["arg1 == arg3"]),fidx=2, offset=6),
    # RuleInstance(Rule("name","i32.add",["arg5", "arg6"],["arg5 != arg6"]),fidx=2, offset=6) # this makes it unsolvable
    ]))

# plugin for overflow
# m.register_plugin(InstructionHookPlugin([RuleInstance(
#     Rule("name","i32.add",["arg1", "arg2"],["arg1>0", "arg2>0", "arg1+arg2 < arg1"]), 
#                                                             fidx=0, offset=2)]))

# # Call the function with symbolic arguments
# params name and size will be returned by wassail 
param_specs = [Param("a", 32),Param("b", 32)]
m.invoke_by_index(2, param_generator, param_specs)
m.run()

# Save a copy of the inputs to the disk
# m.finalize()

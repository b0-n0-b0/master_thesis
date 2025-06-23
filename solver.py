from manticore.wasm import ManticoreWASM, types
from manticore.core.plugin import Plugin
from utils.rule_parser_lark import RuleMatch, Rule

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

    # TODO: check if the state contains all the reachability constraints or not
    # NOTE: apply at end version
    # def generic_solver(self, state, current_instruction):
    #     if len(self.rule_instances) > 0:
    #         current_rule = self.rule_instances[self.current_rule_idx]
    #         # we reverse the array because WASM is a stack machine (last pushed value is the last param of the instruction)
    #         # match target instruction
    #         if current_instruction.funcaddr == current_rule.fidx and current_instruction.offset == current_rule.offset:
    #             # we found the rule match, we can proceed to the next one
    #             symbolic_parameters = []
    #             # create parameters starting from the rule
    #             for idx, param in enumerate(current_rule.rule.parameters[::-1]):
    #                 symbolic_parameters.append(state.stack.peek_nth(idx+1))
    #             current_rule.symbolic_parameters = symbolic_parameters
    #             # NOTE: moving the constraint evaluation to the end allows for more complex constraints; we can i.e. enforce 
    #             # constraints that involve parameters of different instructions
    #             # we've met all the rules, now we apply all the constraints and solve for the function params
    #             if self.current_rule_idx == len(self.rule_instances)-1:
    #                 # define all the parameters
    #                 for rule_instance in self.rule_instances:
    #                     for idx, parameter in enumerate(rule_instance.rule.parameters[::-1]):
    #                         print(f"param {parameter} -> {rule_instance.symbolic_parameters[idx]}")
    #                         locals()[parameter] = rule_instance.symbolic_parameters[idx] 
    #                 # apply all the constraints
    #                 for rule_instance in self.rule_instances:
    #                      for constraint in rule_instance.rule.constraints:
    #                         print(constraint)
    #                         state.constrain(eval(constraint))
    #                 # solve
    #                 for sym in state.input_symbols:
    #                     solved = state.solve_n(sym,1)
    #                     print(f"solution for {sym.name}: {solved}")
    #                 print(state)
    #             self.current_rule_idx += 1
    # TODO: check if the state contains all the reachability constraints or not
    # NOTE: apply at match
    def generic_solver(self, state, current_instruction):
        if len(self.rule_instances) > 0:
            current_rule = self.rule_instances[self.current_rule_idx]
            if current_instruction.funcaddr == current_rule.fidx and current_instruction.offset == current_rule.offset:
                symbolic_parameters = []
                # NOTE: declare parameters starting from the rule
                # we reverse the array because WASM is a stack machine (last pushed value is the last param of the instruction)
                # match target instruction
                for idx, param in enumerate(current_rule.rule.parameters[::-1]):
                    # print(f"param {param} -> {state.stack.peek_nth(idx+1)}")
                    locals()[param] = state.stack.peek_nth(idx+1)
                for constraint in current_rule.rule.constraints:
                    state.constrain(eval(constraint))
                # NOTE: all constraints where applied, we are ready to try and concretize the state
                if self.current_rule_idx == len(self.rule_instances)-1:
                    if (state.is_feasible()):
                        # for c in state._constraints:
                            # print(c)
                            # state.constrain(c)
                        for sym in state.input_symbols:
                            solved = state.solve_one(sym)
                            print(f"solution for {sym.name}: {solved}")
                    # print(dir(state))
                # NOTE: we found the rule match, we can proceed to the next one
                self.current_rule_idx += 1

    def will_execute_instruction_callback(self, state, *args):
        # self.example_solver_for_add_if(state, *args)
        instruction = args[0]
        # print(f"In function: {instruction.funcaddr} executing {instruction.mnemonic} @ offset {instruction.offset}")
        self.generic_solver(state, instruction)

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

def run_symbolic_execution(module, rule_match_list, function_index):
    # Initialize ManticoreWASM with the target WebAssembly file
    m = ManticoreWASM("../tests/hello_world/hello_world.wasm")
    # TODO: what about non-numeric parameters? 
    types = m.get_params_by_func_index(function_index)[0]
    param_specs = []
    for idx, type in enumerate(types):
        param_specs.append(Param(f"param_{idx}", type.get_size()))
    # Register our instruction execution hook
    # The Rule is provided by the RuleSet, fidx and offset are provided by the wassail output 
    m.register_plugin(InstructionHookPlugin(rule_match_list))
    # # Call the function with symbolic arguments
    m.invoke_by_index(function_index, param_generator, param_specs)
    m.run()
    m.finalize()

if __name__ == "__main__":
    m = ManticoreWASM("../tests/hello_world/hello_world.wasm")
    m.register_plugin(InstructionHookPlugin([
        RuleMatch(Rule("name","i32.add",["arg3", "arg4"],["arg3 == 19", "arg3 > 0"]),fidx=2, offset=6),
        RuleMatch(Rule("name","i32.add",["arg5", "arg6"],["arg5 != 0"]),fidx=2, offset=20),
        ]))
    types = m.get_params_by_func_index(function_index)[0]
    param_specs = []
    for idx, type in enumerate(types):
        param_specs.append(Param(f"param_{idx}", type.get_size()))
    m.invoke_by_index(2, param_generator, param_specs)
    m.run()
    m.finalize()


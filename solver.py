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
        self.match_constraints = []

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
                    locals()[param] = state.stack.peek_nth(idx+1)
                for constraint in current_rule.rule.constraints:
                    state.constrain(eval(constraint))
                # NOTE: all constraints where applied, we are ready to try and concretize the state
                if self.current_rule_idx == len(self.rule_instances)-1:
                    if (state.is_feasible()):
                        # NOTE: can we actually have more then one list of constraints?
                        self.match_constraints.append(state._constraints)
                        # for sym in state.input_symbols:
                        #     solved = state.solve_one(sym)
                        #     print(f"solution for {sym.name}: {solved}")
                    else:
                        print("not feasible", flush=True)
                    # NOTE: abandon the state once done
                    state.abandon()
                    # print(dir(state))
                # NOTE: we found the rule match, we can proceed to the next one
                self.current_rule_idx += 1

    def will_execute_instruction_callback(self, state, *args):
        # self.example_solver_for_add_if(state, *args)
        instruction = args[0]
        # print(f"In function: {instruction.funcaddr} executing {instruction.mnemonic} @ offset {instruction.offset}", flush=True)
        self.generic_solver(state, instruction)

class CallHookPlugin(Plugin):
    def __init__(self, target_function_call):
        super().__init__()
        self.target_call = target_function_call
        # solve for the input symbols once these are over
        self.match_constraints = []
    def will_call_function_callback(self, state, *args):
        called_function = args[0]
        if (called_function == self.target_call and state.is_feasible()):
            # NOTE: can we actually have more then one list of constraints?
            self.match_constraints.append(state._constraints)
        # print(f"will call function {called_function}")



# In order to invoke a wasm fuction with symbolic parameters, 
# we use a function that returns an array of symbolic values 
# with types compatibles with the function signature
def param_generator(state, params):
    sym_params = []
    for param in params:
        sym_params.append(state.new_symbolic_value(param.size, param.name))
    return sym_params

def run_symbolic_execution(module, function_index, plugin):
    # NOTE: Initialize ManticoreWASM with the target WebAssembly file
    m = ManticoreWASM(module)
    types = m.get_params_by_func_index(function_index)[0]
    param_specs = []
    for idx, type in enumerate(types):
        param_specs.append(Param(f"param_{idx}", type.get_size()))
    # NOTE: Register our instruction execution hook
    # NOTE: The Rule is provided by the RuleSet, fidx and offset are provided by the wassail output 
    m.register_plugin(plugin)
    # NOTE: Call the function with symbolic arguments
    m.invoke_by_index(function_index, param_generator, param_specs)
    m.run()
    m.finalize()
    return plugin.match_constraints

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
    


from manticore.wasm import ManticoreWASM, types
from manticore.core.plugin import Plugin
from utils.rule_parser_lark import RuleMatch, Rule

class Param():
    def __init__(self, name, size):
        self.name = name
        self.size = size

class InstructionHookPlugin(Plugin):
    """A plugin that hooks the instruction execution and applies constraints specified in the rule file"""

    def __init__(self, rule_instances):
        super().__init__()
        # solve for the input symbols once these are over
        self.rule_instances = rule_instances
        self.match_constraints = []

    # NOTE: apply at match
    def generic_solver(self, state, current_instruction):
        with self.locked_context("counter", dict) as ctx:
            current_rule_idx = ctx.setdefault("current_rule_idx", 0)

        # NOTE: abandon ALL the states once done
        if current_rule_idx > len(self.rule_instances)-1:
            state.abandon()
        
        if len(self.rule_instances) > 0:
            current_rule = self.rule_instances[current_rule_idx]
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
                if current_rule_idx == len(self.rule_instances)-1:
                    if (state.is_feasible()):
                        self.match_constraints.append(state._constraints)
                
                # NOTE: we found the rule match, we can proceed to the next one
                with self.locked_context("counter", dict) as ctx:
                    ctx['current_rule_idx'] += 1

    def will_execute_instruction_callback(self, state, *args):
        """ callback for the will_execute_instruction event"""

        instruction = args[0]
        self.generic_solver(state, instruction)

class CallHookPlugin(Plugin):
    """A plugin that hooks the execution of both call and call_indirect in order to find constraints related to a specific edge in the callgraph"""

    def __init__(self, target_function_call, target_src):
        super().__init__()
        self.target_call = target_function_call
        self.target_src = target_src
        self.match_constraints = []
    def will_call_function_callback(self, state, *args):
        called_function, current_function = args
        if (current_function == self.target_src and called_function == self.target_call and state.is_feasible()):
            self.match_constraints.append(state._constraints)

def param_generator(state, params):
    """Symbolic parameter generator"""
    sym_params = []
    for param in params:
        sym_params.append(state.new_symbolic_value(param.size, param.name))
    return sym_params

def run_symbolic_execution(module, function_index, plugin):
    """Execute the function identified by function_index of the specified module with the specified plugin."""
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
    # m.finalize()
    return plugin.match_constraints


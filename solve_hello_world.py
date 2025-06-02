from manticore.wasm import ManticoreWASM, types
from manticore.core.plugin import Plugin

class Rule():
    def __init__(target_instruction, parameters, constraints=[]):
        # mnemonic target
        self.target_instruction = target_instruction
        # list of target's instruction parameters (with names) 
        self.parameters = parameters
        # list of constraints to apply
        self.constraints = constraints

class PrintRetPlugin(Plugin):
    """A plugin that looks for states that returned SOMETHING and solves for their inputs"""

    def generic_solver(self, state, current_instruction, target_fidx, target_offset, constraints=[], parameters=[]):
        # create parameters starting from the rule
        # we reverse the array because WASM is a stack machine (last pushed value is the last param of the instruction)
        for idx, param in enumerate(parameters[::-1]):
            locals()[param]=state.stack.peek_nth(idx+1) 
        # match target instruction
        if current_instruction.funcaddr == target_fidx and current_instruction.offset == target_offset:
            # apply constraints
            for constraint in constraints:
                state.constrain(eval(constraint))
            print("Solution found!")
            for sym in state.input_symbols:
                solved = state.solve_n(sym,1)
                print(f"{sym.name}: {solved}")

    def will_execute_instruction_callback(self, state, *args):
        # self.example_solver_for_add_if(state, *args)
        instruction = args[0]
        self.generic_solver(state, instruction, target_fidx=0, target_offset=2, 
                            constraints=["arg1>0", "arg2>0", "arg1+arg2 < arg1"], parameters=["arg1", "arg2"])
        # print(f"In function: {instruction.funcaddr} executing {instruction.mnemonic} @ offset {instruction.offset}")




# in order to invoke a wasm fuction with symbolic parameters, 
# we use a function that returns an array of symbolic values 
# with types compatibles with the function signature
def param_generator(state):
    # contains also non exported functions (if ever used)
    a = state.new_symbolic_value(32,"a")
    b = state.new_symbolic_value(32,"b")
    # state.constrain(a == 2147483647)
    return [a,b]

# Initialize ManticoreWASM with the target WebAssembly file
m = ManticoreWASM("./hello_world.wasm")
# print(m)
# Register our state termination callback
m.register_plugin(PrintRetPlugin())

# # Call the `add` function with two symbolic arguments
m.invoke_by_index(2, param_generator)
m.run()

# Save a copy of the inputs to the disk
# m.finalize()

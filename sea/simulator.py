import dis

from sea.bytecode import get_instr_properties
from sea.virtuals import Call, Constant, Virtual, traverse_virtuals


def simulate(instructions):
    calls = []
    stack = []

    for instr in instructions:
        properties = get_instr_properties(instr)

        arguments = [
            stack.pop(index) for index in range(properties.negative_effect, 0)
        ]
        assert all(
            isinstance(argument, Virtual) for argument in arguments
        ), "real object leaked into the stack"

        # If the instruction has an oparg, then it is going
        # to take the first slot.
        if instr.arg is not None:
            arguments.insert(0, Constant(instr.argval))

        call = Call(instr, arguments)
        calls.append(call)

        if properties.positive_effect:
            # TODO: ...
            stack.append(call)

    assert len(stack) == 0, stack
    return traverse_virtuals(calls)


def simulate_source(source_code):
    instructions = tuple(dis.Bytecode(source_code))
    return simulate(instructions)

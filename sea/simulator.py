from sea.bytecode import InstructionProperties
from sea.ir import compile_ir
from sea.virtuals import Block, Call, Constant, Virtual


def simulate(instructions, jump=None):
    calls = []
    stack = []

    for instr in instructions:
        properties = InstructionProperties(instr, jump=jump)

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

    if len(stack) > 0:
        print("\n".join(obj.as_string() for obj in stack))
        raise ValueError("stack is not empty")

    return calls


def simulate_ir(instructions):
    real_blocks = compile_ir(instructions)

    r2v_map = {}

    for real_block in real_blocks:
        virtual_calls = simulate(
            real_block.instructions,
        )
        r2v_map[real_block.block_id] = Block(
            real_block,
            virtual_calls,
            labels=real_block.labels,
        )

    for _, block in r2v_map.items():
        for next_real_block in block.block.next_blocks:
            block.next_blocks.append(r2v_map[next_real_block.block_id])

    blocks = list(r2v_map.values())
    return blocks

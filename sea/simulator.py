from collections import deque
from typing import NamedTuple, Optional, Sequence

from sea.bytecode import InstructionProperties
from sea.ir import IRBlock, compile_ir
from sea.virtuals import Block, Call, Constant, Partial, Virtual


def _simulate(instructions, *, is_jump=None, starter_stack=()):
    calls = []
    stack = [*starter_stack]

    for instr in instructions:
        properties = InstructionProperties(instr, jump=is_jump)

        arguments = [
            stack.pop(index)
            if len(stack) >= abs(index)
            else Constant("<NULL>")
            for index in range(properties.negative_effect, 0)
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

        positive_effect = properties.positive_effect
        if positive_effect == 1:
            stack.append(call)
        elif positive_effect > 1:
            stack.extend(
                Partial(call, index) for index in range(positive_effect)
            )

    return stack, calls


def simulate(instructions):
    """Simulate given instructions and return a list of
    virtual calls in the Basic SEA form."""
    stack, calls = _simulate(instructions)
    if len(stack) > 0:
        print("\n".join(obj.as_string() for obj in stack))
        raise ValueError("stack is not empty")

    return calls


class ParentBlock(NamedTuple):
    block: IRBlock
    spilled_stack: Sequence[Call] = ()
    is_jump: Optional[bool] = None


def simulate_ir(instructions):
    """Simulate given instructions and return a list of
    CFG blocks."""
    r2v_map = {}
    parent_block = ParentBlock(compile_ir(instructions))

    seen_blocks = {parent_block.block.block_id}
    parent_blocks = deque([parent_block])

    while parent_blocks:
        real_block, spilled_stack, is_jump = parent_blocks.popleft()
        stack, virtual_calls = _simulate(
            real_block.instructions,
            starter_stack=spilled_stack,
            is_jump=is_jump,
        )
        r2v_map[real_block.block_id] = Block(
            real_block, virtual_calls, labels=real_block.labels
        )

        for next_block, metadata in zip(
            real_block.next_blocks, real_block.metadata
        ):
            if next_block.block_id not in seen_blocks:
                parent_block = ParentBlock(
                    next_block, spilled_stack=stack, is_jump=metadata["fall"]
                )
                parent_blocks.append(parent_block)
                seen_blocks.add(next_block.block_id)

    for _, block in r2v_map.items():
        for next_real_block in block.block.next_blocks:
            block.next_blocks.append(r2v_map[next_real_block.block_id])

    blocks = list(r2v_map.values())
    return blocks

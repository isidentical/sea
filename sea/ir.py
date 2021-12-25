# An experimental IR based on basic blocks (not used anywhere
# at the moment).

from __future__ import annotations

import dis
from collections import deque
from dataclasses import dataclass, field
from functools import cache, partial
from typing import Any, Dict, List, Optional

import opcode


def is_jump(instr):
    return instr.opcode in opcode.hasjabs + opcode.hasjrel


def is_conditional_jump(instr):
    return instr.opname not in ("JUMP_ABSOLUTE", "JUMP_FORWARD")


def is_backwards_jump(program_counter, instr):
    return (instr.argval // 2) < program_counter


@dataclass
class IRBlock:
    instructions: List[dis.Instruction] = field(default_factory=list)

    # Assigned by the numerator
    block_id: int = -1

    # Assigned by the linker
    next_blocks: List[Block] = field(default_factory=list)
    metadata: List[Dict[str, Any]] = field(default_factory=list)

    def __bool__(self):
        return bool(self.instructions)

    def add_instruction(self, instr):
        self.instructions.append(instr)

    def dump(self):
        lines = []
        for instr in self.instructions:
            lines.append(f"   {instr.offset} {instr.opname}({instr.argval})")

        return "\n".join(lines)

    @property
    def offset_range(self):
        return range(
            self.instructions[0].offset,
            self.instructions[-1].offset
            + 1,  # right operand is not inclusive on range()
        )

    @property
    def name(self):
        assert self.block_id != -1
        return f"B{self.block_id}"

    @property
    def labels(self):
        return [metadata.get("label") for metadata in self.metadata]


def _transform(instructions, *, counter=0, end_range=-1):
    blocks = [IRBlock()]

    instr = None

    while counter < end_range:
        cursor = blocks[-1]
        instr = instructions[counter]

        if is_jump(instr) and not is_backwards_jump(counter, instr):
            iteration = 0
            final_counter = instr.argval // 2
            while final_counter is not None:
                target_counter = final_counter
                final_counter, target_blocks = _transform(
                    instructions,
                    counter=counter + 1,
                    end_range=final_counter,
                )
                blocks.extend(target_blocks)
                counter = final_counter or target_counter
                iteration += 1

            counter -= 1
            blocks.append(IRBlock())

        cursor.add_instruction(instr)
        counter += 1

    # If the last instruction contains a jump, then propagate this
    # to the upper level
    if (
        (instr is not None)
        and is_jump(instr)
        and not is_backwards_jump(counter, instr)
    ):
        final_counter = instr.argval // 2
    else:
        final_counter = None

    return final_counter, blocks


def _assign_ids(original_blocks):
    blocks = []
    for block_id, block in enumerate(
        filter(lambda block: block, original_blocks)
    ):
        block.block_id = block_id
        blocks.append(block)

    return blocks


def _eliminate_duplicates(original_blocks):
    blocks = {tuple(block.instructions): block for block in original_blocks}
    return list(blocks.values())


def _link(blocks):
    @cache
    def find_block(offset):
        for block in blocks:
            if offset in block.offset_range:
                return block

    def get_label(instr, fall):
        if "_IF_FALSE" in instr.opname:
            label_1 = "true"
            label_2 = "false"
        elif "_IF_TRUE" in instr.opname:
            label_1 = "false"
            label_2 = "true"
        elif "FOR_ITER" in instr.opname:
            label_1 = "loop"
            label_2 = "exhaust"
        else:
            label_1 = label_2 = None

        if fall:
            return label_1
        else:
            return label_2

    def follow_block(block, last_instr, follower_block, fall=False):
        if follower_block is not None:
            block.next_blocks.append(follower_block)

            metadata = {"label": get_label(last_instr, fall), "fall": fall}
            block.metadata.append(metadata)

    for block in blocks:
        follow = partial(follow_block, block)
        last_instr = block.instructions[-1]

        if is_jump(last_instr):
            follow(last_instr, find_block(last_instr.argval))
            # If the last instruction ends with a non-conditional jump, then
            # we can't link the following block
            if not is_conditional_jump(last_instr):
                continue

        follow(last_instr, find_block(last_instr.offset + 2), fall=True)

    return blocks


def _filter_unreachable_blocks(original_blocks):
    start_block = original_blocks[0]

    seen_blocks = {start_block.block_id}
    stack = deque([start_block])
    while stack:
        block = stack.popleft()

        for next_block in block.next_blocks:
            if next_block.block_id not in seen_blocks:
                seen_blocks.add(next_block.block_id)
                stack.append(next_block)

    return [
        possible_block
        for possible_block in original_blocks
        if possible_block.block_id in seen_blocks
    ]


def compile_ir(instructions):
    _, blocks = _transform(instructions, end_range=len(instructions))
    blocks = _eliminate_duplicates(blocks)
    blocks = _assign_ids(blocks)
    blocks = _link(blocks)
    blocks = _filter_unreachable_blocks(blocks)

    assert len(blocks) >= 1
    return blocks[0]

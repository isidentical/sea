# Experimental SEA IR (not used anywhere)

from __future__ import annotations

import dis
import sys
from dataclasses import dataclass, field
from typing import Tuple

import opcode


def has_jump(instr):
    return instr.opcode in opcode.hasjabs + opcode.hasjrel


@dataclass
class Block:
    instructions: List[dis.Instruction] = field(default_factory=list)
    next_block: Block = None

    def __bool__(self):
        return bool(self.instructions)

    def add_instruction(self, instr):
        self.instructions.append(instr)

    @property
    def start_offset(self):
        return self.instructions[0].offset


def _transform(instructions, *, counter=0, start_range=-1, end_range=-1):
    blocks = [Block()]

    instr = None

    while start_range <= counter < end_range:
        cursor = blocks[-1]
        instr = instructions[counter]

        if has_jump(instr):
            iteration = 0
            final_counter = instr.argval // 2
            while final_counter is not None:
                target_counter = final_counter
                final_counter, target_blocks = _transform(
                    instructions,
                    counter=counter + 1,
                    start_range=counter + 1,
                    end_range=final_counter,
                )
                blocks.extend(target_blocks)
                counter = final_counter or target_counter
                iteration += 1

            counter -= 1
            blocks.append(Block())

        cursor.add_instruction(instr)
        counter += 1

    # If the last instruction contains a jump, then propagate this
    # to the upper level
    if (instr is not None) and has_jump(instr):
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


def _link(blocks):
    offset_map = {block.start_offset: block for block in blocks}

    for block in blocks:
        last_instr = block.instructions[-1]
        if has_jump(last_instr):
            next_block = offset_map.get(last_instr.argval)
        else:
            next_block = offset_map.get(last_instr.offset + 2)

        block.next_block = next_block

    return blocks


def transform(instructions):
    _, blocks = _transform(instructions, end_range=len(instructions))
    blocks = _assign_ids(blocks)
    blocks = _link(blocks)

    for block in blocks:
        source = f"{block.block_id}. block"
        if block.next_block:
            source += f" (proceeds to {block.next_block.block_id})"
        else:
            source += " (exit block)"
        print(source + ": ")
        for instr in block.instructions:
            print(f"   {instr.offset} {instr.opname}({instr.argval})")


def transform_source(source_code):
    instructions = list(dis.Bytecode(source_code))
    return transform(instructions)


if __name__ == "__main__":
    with open(sys.argv[1]) as stream:
        print(transform_source(stream.read()))

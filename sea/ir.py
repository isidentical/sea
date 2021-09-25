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

    def __bool__(self):
        return bool(self.instructions)

    def add_instruction(self, instr):
        self.instructions.append(instr)


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

    return final_counter, filter(lambda block: block, blocks)


def transform(instructions):
    _, blocks = _transform(instructions, end_range=len(instructions))

    for index, block in enumerate(blocks):
        print(f"{index}. block: ")
        for instr in block.instructions:
            print(f"   {instr.offset} {instr.opname}({instr.argval})")


def transform_source(source_code):
    instructions = list(dis.Bytecode(source_code))
    return transform(instructions)


if __name__ == "__main__":
    with open(sys.argv[1]) as stream:
        print(transform_source(stream.read()))

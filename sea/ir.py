# An experimental IR based on basic blocks (not used anywhere
# at the moment).

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

    # Assigned by the linker
    next_block: Block = None
    block_id: int = -1

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
    def start_offset(self):
        return self.instructions[0].offset

    @property
    def name(self):
        assert self.block_id != -1
        return f"B{self.block_id}"


def _transform(instructions, *, counter=0, end_range=-1):
    blocks = [Block()]

    instr = None

    while counter < end_range:
        cursor = blocks[-1]
        instr = instructions[counter]

        if has_jump(instr):
            iteration = 0
            final_counter = instr.argval // 2
            # TODO: support loops
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


def _eliminate_duplicates(original_blocks):
    blocks = {tuple(block.instructions): block for block in original_blocks}
    return list(blocks.values())


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
    blocks = _eliminate_duplicates(blocks)
    blocks = _assign_ids(blocks)
    blocks = _link(blocks)
    return blocks


def transform_source(source_code):
    instructions = list(dis.Bytecode(source_code))
    return transform(instructions)


def dump(blocks):
    for block in blocks:
        source = f"{block.block_id}. block"
        if block.next_block:
            source += f" (proceeds to {block.next_block.block_id})"
        else:
            source += " (exit block)"
        print(source + ": ")
        print(textwrap.dedent("   ", block.dump()))


def visualize(blocks):
    import graphviz

    board = graphviz.Digraph()

    for block in blocks:
        board.node(block.name, block.name + "\n" + block.dump())
        if block.next_block:
            board.edge(block.name, block.next_block.name)

    board.render("/tmp/ir_out.gv", view=True)


if __name__ == "__main__":
    with open(sys.argv[1]) as stream:
        visualize(transform_source(stream.read()))

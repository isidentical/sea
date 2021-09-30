# An experimental IR based on basic blocks (not used anywhere
# at the moment).

from __future__ import annotations

import dis
import sys
import textwrap
from argparse import ArgumentParser
from dataclasses import dataclass, field
from functools import cache, partial
from typing import Tuple

import opcode


def has_jump(instr):
    return instr.opcode in opcode.hasjabs + opcode.hasjrel


def has_conditional_jump(instr):
    return has_jump(instr) and (
        "_IF_" in instr.opname
        or "SETUP_" in instr.opname
        or "FOR_ITER" == instr.opname
    )  # pretty hacky, come with a better way.


def is_backwards_jump(program_counter, instr):
    return (instr.argval // 2) < program_counter


@dataclass
class Block:
    instructions: List[dis.Instruction] = field(default_factory=list)

    # Assigned by the linker
    next_blocks: List[Block] = field(default_factory=list)
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


def _transform(instructions, *, counter=0, end_range=-1):
    blocks = [Block()]

    instr = None

    while counter < end_range:
        cursor = blocks[-1]
        instr = instructions[counter]

        if has_jump(instr) and not is_backwards_jump(counter, instr):
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
            blocks.append(Block())

        cursor.add_instruction(instr)
        counter += 1

    # If the last instruction contains a jump, then propagate this
    # to the upper level
    if (
        (instr is not None)
        and has_jump(instr)
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

    def follow_block(block, follower_block):
        if follower_block is not None:
            block.next_blocks.append(follower_block)

    for block in blocks:
        follow = partial(follow_block, block)
        last_instr = block.instructions[-1]

        if has_jump(last_instr):
            follow(find_block(last_instr.argval))

        # If the last instruction ends with a non-conditional jump, then
        # we can't link, otherwise we do.
        if has_conditional_jump(last_instr) or not has_jump(last_instr):
            follow(find_block(last_instr.offset + 2))

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
        if block.next_blocks:
            next_blocks = ", ".join(
                str(next_block.block_id)
                for next_block in sorted(
                    block.next_blocks,
                    key=lambda block: block.block_id,
                    reverse=True,
                )
            )
            source += f" (proceeds to {next_blocks})"
        else:
            source += " (exit block)"
        print(source + ": ")
        print(textwrap.indent(block.dump(), "    "))


def visualize(blocks):
    import graphviz

    board = graphviz.Digraph()

    for block in blocks:
        board.node(block.name, block.name + "\n" + block.dump())
        for next_block in block.next_blocks:
            board.edge(block.name, next_block.name)

    board.render("/tmp/ir_out.gv", view=True)


def main():
    parser = ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--show-graph", action="store_true")

    options = parser.parse_args()

    with open(options.file) as stream:
        source_code = stream.read()

    blocks = transform_source(source_code)
    if options.show_graph:
        visualize(blocks)
    else:
        dump(blocks)


if __name__ == "__main__":
    main()

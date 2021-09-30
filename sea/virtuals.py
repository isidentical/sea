from __future__ import annotations

import dis
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, List

if TYPE_CHECKING:
    from sea.ir import IRBlock


class Virtual:
    PREFIX = ""

    def __post_init__(self):
        self.virtual_id = -1

    @property
    def name(self):
        assert self.virtual_id != -1
        return "$" + self.PREFIX + str(self.virtual_id)

    def as_render(self):
        raise NotImplementedError


@dataclass
class Block(Virtual):
    PREFIX: ClassVar[str] = "B"

    block: IRBlock
    calls: List[Call]
    next_blocks: List[Block] = field(default_factory=list)

    def as_string(self):
        lines = []
        lines.append(f"Block {self.name}: ")
        for call in self.calls:
            lines.append("    " + call.as_string())
        if self.next_blocks:
            may_jump_to = ", ".join(
                next_block.name for next_block in self.next_blocks
            )
            lines.append(f"    may jump to: {may_jump_to}")
        return "\n".join(lines)


@dataclass
class Call(Virtual):
    func: dis.Instruction
    arguments: List[Virtual]

    def as_string(self):
        source = self.name
        source += " = "
        source += self.func.opname
        source += "("
        source += ", ".join(
            argument.name
            if isinstance(argument, Call)
            else argument.as_string()
            for argument in self.arguments
        )
        source += ")"
        return source


@dataclass
class Constant(Virtual):
    PREFIX: ClassVar[str] = "C"

    value: Any

    def as_string(self):
        return repr(self.value)


def traverse_virtuals(virtuals, *, counter=None):
    if counter is None:
        counter = Counter()

    for virtual in virtuals:
        if virtual.virtual_id != -1:
            continue

        virtual.virtual_id = counter[virtual.PREFIX]
        if isinstance(virtual, Call):
            traverse_virtuals(virtual.arguments, counter=counter)
        elif isinstance(virtual, Block):
            traverse_virtuals(virtual.calls, counter=counter)

        counter[virtual.PREFIX] += 1

    return virtuals

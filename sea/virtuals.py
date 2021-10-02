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
        return "$" + self.PREFIX + str(self.virtual_id)

    def as_render(self):
        raise NotImplementedError


@dataclass
class Block(Virtual):
    PREFIX: ClassVar[str] = "B"

    block: IRBlock
    calls: List[Call]
    next_blocks: List[Block] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)

    def find_jump_target(self, offset):
        for call in self.calls:
            if call.func.offset == offset:
                return call

    def as_string(self):
        lines = []
        lines.append(f"Block {self.name}: ")
        for call in self.calls:
            lines.append("    " + call.as_string())
        if self.next_blocks:
            parts = []
            for label, next_block in zip(self.labels, self.next_blocks):
                part = next_block.name
                if label:
                    part += f" (on {label})"
                parts.append(part)
            lines.append(f"    may jump to: {', '.join(parts)}")
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
class Partial(Virtual):
    PREFIX: ClassVar[str] = "P"

    call: Call
    index: int

    def as_string(self):
        return f"{self.call.name}[{self.index}]"


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

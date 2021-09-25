import dis
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, ClassVar, List


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

        counter[virtual.PREFIX] += 1

    return virtuals

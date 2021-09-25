from __future__ import annotations

import dis
import sys
from dataclasses import dataclass
from typing import Any, List

import opcode


@dataclass
class VirtualInstruction:
    name: str
    arguments: List[str]

    idx: int = -1

    def as_string(self):
        source = "$" + str(self.idx)
        source += " = "
        source += self.name
        source += "("
        source += ", ".join(
            argument.as_string() for argument in self.arguments
        )
        source += ")"
        return source


@dataclass
class VirtualConstant:
    value: Any

    def as_string(self):
        return repr(self.value)


@dataclass
class Reference:
    referee: VirtualInstruction

    def as_string(self):
        return f"${self.referee.idx}"


@dataclass
class InstructionProperties:
    instr: dis.Instruction
    negative_effect: int = 0
    uses_argument: bool = False

    @property
    def positive_effect(self):
        # net_effect = positive_effect + negative_effect
        return self.net_effect + self.negative_effect

    @property
    def net_effect(self):
        return opcode.stack_effect(self.instr.opcode, self.instr.arg)


def get_instr_properties(instr):
    properties = InstructionProperties(instr)

    if instr.opname.startswith("LOAD_"):
        if instr.opname in ("LOAD_ATTR", "LOAD_METHOD"):
            properties.negative_effect = 1
    elif instr.opname.startswith("BINARY_"):
        properties.negative_effect = 2
    elif instr.opname in ("POP_TOP", "RETURN_VALUE"):
        properties.negative_effect = 1
    else:
        raise NotImplementedError(instr.opcode)

    return properties


def simulate_stack(source):
    stack = []
    virtual_instructions = []

    for instr in dis.Bytecode(source):
        properties = get_instr_properties(instr)

        arguments = []
        for _ in range(properties.negative_effect):
            virtual_object = stack.pop()
            if isinstance(virtual_object, VirtualInstruction):
                arguments.append(Reference(virtual_object))
            elif isinstance(virtual_object, VirtualConstant):
                arguments.append(virtual_object)
            else:
                raise NotImplementedError(
                    f"Real object leaked into the arguments: {virtual_object!r}"
                )

        if instr.opcode > opcode.HAVE_ARGUMENT:
            arguments.append(VirtualConstant(instr.argval))

        virtual_instr = VirtualInstruction(instr.opname, arguments=arguments)
        virtual_instructions.append(virtual_instr)
        if properties.positive_effect:
            stack.append(virtual_instr)

    assert len(stack) == 0, stack

    return virtual_instructions


def assign_ids(virtual_instructions, *, counter=0):
    for virtual_instr in virtual_instructions:
        virtual_instr.idx = counter
        counter += 1


def main():
    virtual_instructions = simulate_stack(sys.argv[1])
    assign_ids(virtual_instructions)

    for virtual_instr in virtual_instructions:
        print(virtual_instr.as_string())


if __name__ == "__main__":
    main()

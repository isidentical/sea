from __future__ import annotations

import dis
import sys
from argparse import ArgumentParser
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, List

import opcode


class Virtual:
    def as_render(self):
        raise NotImplementedError


@dataclass
class VirtualInstruction(Virtual):
    name: str
    arguments: List[str]

    instr: dis.Instruction = field(repr=False, compare=False)

    idx: int = -1

    def as_string(self):
        source = self.ref_name
        source += " = "
        source += self.name
        source += "("
        source += ", ".join(
            argument.as_string() for argument in self.arguments
        )
        source += ")"
        return source

    @property
    def ref_name(self):
        return "$" + str(self.idx)


@dataclass
class VirtualConstant(Virtual):
    value: Any

    def as_string(self):
        return repr(self.value)


@dataclass
class Reference:
    referee: VirtualInstruction

    def as_string(self):
        return self.referee.ref_name


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


def assign_ids(virtual_instructions, *, counter=0):
    for virtual_instr in virtual_instructions:
        virtual_instr.idx = counter
        counter += 1

    return virtual_instructions


KNOWN_NEGATIVE_EFFECTS = {
    "COMPARE_OP": 2,
    "POP_TOP": 1,
    "RETURN_VALUE": 1,
    "POP_JUMP_IF_FALSE": 1,
    "POP_JUMP_IF_TRUE": 1,
    "JUMP_FORWARD": 0,
}


def get_instr_properties(instr):
    properties = InstructionProperties(instr)

    if instr.opname.startswith("LOAD_"):
        if instr.opname in ("LOAD_ATTR", "LOAD_METHOD"):
            properties.negative_effect = 1
    elif instr.opname.startswith("STORE_"):
        if instr.opname == "STORE_ATTR":
            properties.negative_effect = 2
        properties.negative_effect = 1
    elif instr.opname.startswith("BINARY_"):
        properties.negative_effect = 2
    elif instr.opname == "CALL_FUNCTION":
        properties.negative_effect = instr.argval + 1
    elif instr.opname in KNOWN_NEGATIVE_EFFECTS:
        properties.negative_effect = KNOWN_NEGATIVE_EFFECTS[instr.opname]
    else:
        raise NotImplementedError(instr.opname)

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

        virtual_instr = VirtualInstruction(
            instr.opname, arguments=arguments, instr=instr
        )
        virtual_instructions.append(virtual_instr)
        if properties.positive_effect:
            stack.append(virtual_instr)

    assert len(stack) == 0, stack

    return assign_ids(virtual_instructions)


def reduce_graph(board, virtual_instructions, outgoing_edges):
    # Patch unconnected edges, not a CFG!
    for instr, next_instr in zip(
        virtual_instructions, virtual_instructions[1:]
    ):
        if instr.ref_name in outgoing_edges:
            continue

        board.edge(
            instr.ref_name, next_instr.ref_name, arrowhead="none", color="gray"
        )
    return board


def show_graph(virtual_instructions):
    import graphviz

    board = graphviz.Digraph()

    outgoing_edges = set()
    for instr in virtual_instructions:
        board.node(instr.ref_name, instr.as_string())

        for argument in instr.arguments:
            if not isinstance(argument, Reference):
                continue

            board.node(argument.as_string(), argument.referee.as_string())
            board.edge(argument.as_string(), instr.ref_name, color="red")
            outgoing_edges.add(argument.as_string())

    reduce_graph(board, virtual_instructions, outgoing_edges)

    board.render("/tmp/out.gv", view=True)


def show_text(virtual_instructions):
    for virtual_instr in virtual_instructions:
        print(virtual_instr.as_string())


def main():
    parser = ArgumentParser()
    parser.add_argument("file", help="source file")
    parser.add_argument("--show-graph", action="store_true")

    options = parser.parse_args()

    with open(options.file) as stream:
        source = stream.read()

    virtual_instructions = simulate_stack(source)
    if options.show_graph:
        show_graph(virtual_instructions)
    else:
        show_text(virtual_instructions)


if __name__ == "__main__":
    main()

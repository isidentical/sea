import dis
from dataclasses import dataclass

import opcode

# TODO: add more instructions
KNOWN_NEGATIVE_EFFECTS = {
    "COMPARE_OP": -2,
    "POP_TOP": -1,
    "RETURN_VALUE": -1,
    "POP_JUMP_IF_FALSE": -1,
    "POP_JUMP_IF_TRUE": -1,
    "JUMP_FORWARD": 0,
}


@dataclass
class InstructionProperties:
    instr: dis.Instruction
    negative_effect: int = 0

    @property
    def positive_effect(self):
        # net_effect = positive_effect + negative_effect
        return self.net_effect - self.negative_effect

    @property
    def net_effect(self):
        return opcode.stack_effect(self.instr.opcode, self.instr.arg)


def get_instr_properties(instr):
    properties = InstructionProperties(instr)

    # TODO: add more instructions
    if instr.opname.startswith("LOAD_"):
        if instr.opname in ("LOAD_ATTR", "LOAD_METHOD"):
            properties.negative_effect = -1
    elif instr.opname.startswith("STORE_"):
        if instr.opname == "STORE_ATTR":
            properties.negative_effect = -2
        properties.negative_effect = -1
    elif instr.opname.startswith("BINARY_"):
        properties.negative_effect = -2
    elif instr.opname == "CALL_FUNCTION":
        properties.negative_effect = -(instr.argval + 1)
    elif instr.opname in KNOWN_NEGATIVE_EFFECTS:
        properties.negative_effect = KNOWN_NEGATIVE_EFFECTS[instr.opname]
    else:
        raise NotImplementedError(instr.opname)

    return properties

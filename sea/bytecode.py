import dis
import sys
from dataclasses import dataclass

import opcode

FVS_MASK = 0x4
FVS_HAVE_SPEC = 0x4

HAS_KWARGS = 0x01
HAS_CLOSURE, HAS_ANNOTATIONS, HAS_KWDEFAULTS, HAS_DEFAULTS = (
    0x08,
    0x04,
    0x02,
    0x01,
)


@dataclass
class InstructionProperties:
    instr: dis.Instruction
    jump: bool = False

    @property
    def positive_effect(self):
        # net_effect = positive_effect + negative_effect
        return self.net_effect - self.negative_effect

    @property
    def net_effect(self):
        return opcode.stack_effect(self.instr.opcode, self.instr.arg)

    @property
    def negative_effect(self):
        return compute_negative_effect(
            self.instr.opname, self.instr.arg, jump=self.jump
        )


# Instruction Sets


def family(prefix, effect):
    return dict.fromkeys(
        (name for name in opcode.opname if name.startswith(prefix)), effect
    )


PY39_INSTRUCTION_SET = {
    # POP(lhs, rhs), PUSH(res)
    **family("BINARY_", -2),
    # POP(lhs, rhs), PUSH(res)
    **family("INPLACE_", -2),
    # POP(value), PUSH(VALUE)
    **family("UNARY_", -1),
    # POP($TOS)
    **family("POP_JUMP_IF", -1),
    # POP(exc, val, tb)
    "RERAISE": -3,
    # POP(exc, val, tb)
    "POP_EXCEPT": -3,
    # POP(target, key, value)
    "STORE_SUBSCR": -3,
    # POP(target, key)
    "DELETE_SUBSCR": -2,
    # POP(target, attr)
    "STORE_ATTR": -2,
    # POP(caught_type, target_types)
    "JUMP_IF_NOT_EXC_MATCH": -2,
    # POP(key, value)
    "MAP_ADD": -2,
    # POP(value, receiver), PUSH(res)
    "YIELD_FROM": -2,
    # POP(lhs, rhs), PUSH(res)
    "COMPARE_OP": -2,
    "IS_OP": -2,
    "CONTAINS_OP": -2,
    # POP(from_list, level), PUSH(module)
    "IMPORT_NAME": -2,
    # POP($TOS)
    "POP_TOP": -1,
    # POP($tos)
    "RETURN_VALUE": -1,
    # POP(expr)
    "PRINT_EXPR": -1,
    # POP(from)
    "IMPORT_STAR": -1,
    # POP(value)
    "STORE_NAME": -1,
    "STORE_FAST": -1,
    "STORE_GLOBAL": -1,
    "STORE_DEREF": -1,
    # POP(value)
    "DELETE_ATTR": -1,
    # POP(value)
    "LIST_APPEND": -1,
    "SET_ADD": -1,
    "LIST_EXTEND": -1,
    "SET_UPDATE": -1,
    "DICT_MERGE": -1,
    "DICT_UPDATE": -1,
    # POP(value), PUSH(iterator)
    "GET_ITER": -1,
    "GET_AITER": -1,
    "GET_YIELD_FROM_ITER": -1,
    # POP(value), PUSH(coro)
    "GET_AWAITABLE": -1,
    # POP(list), PUSH(tuple)
    "LIST_TO_TUPLE": -1,
    # POP(value)
    "YIELD_VALUE": -1,
    # POP(object), PUSH(value)
    "LOAD_ATTR": -1,
    # POP(iterator), PUSH(next_value)
    "FOR_ITER": -1,
    # POP(sequence), PUSH(*sequence)
    "UNPACK_SEQUENCE": -1,
    "UNPACK_EX": -1,
    # TODO: DUP_* / ROT_*
}
PY310_INSTRUCTION_SET = {**PY39_INSTRUCTION_SET}

INSTRUCTION_SETS = {
    (3, 9): PY39_INSTRUCTION_SET,
    (3, 10): PY310_INSTRUCTION_SET,
}

try:
    INSTRUCTION_SET = INSTRUCTION_SETS[sys.version_info[:2]]
except KeyError as exc:
    raise ValueError(f"Instruction set is not found for: {sys.version!r}")


def compute_negative_effect(opname, oparg, jump=False):
    if effect := INSTRUCTION_SET.get(opname):
        return effect

    # oparg dependant
    if opname in ("BUILD_STRING", "BUILD_LIST", "BUILD_SET", "BUILD_STRING"):
        return -oparg
    elif opname == "BUILD_MAP":
        return -(2 * oparg)
    elif opname == "BUILD_CONST_KEY_MAP":
        return -oparg - 1
    elif opname == "BUILD_SLICE":
        return -3 if oparg == 3 else -2
    elif opname == "CALL_FUNCTION":
        return -oparg - 1
    elif opname == "CALL_METHOD":
        return -oparg - 2
    elif opname == "CALL_FUNCTION_KW":
        return -oparg - 2
    elif opname == "CALL_FUNCTION_EX":
        return -2 - (oparg & HAS_KWARGS)
    elif opname == "FORMAT_VALUE":
        return -2 if (oparg & FVS_MASK) == FVS_HAVE_SPEC else -1
    elif opname == "MAKE_FUNCTION":
        effect = -2
        for flag in (
            HAS_CLOSURE,
            HAS_ANNOTATIONS,
            HAS_KWDEFAULTS,
            HAS_DEFAULTS,
        ):
            if oparg & flag:
                effect -= 1
        return effect
    elif opname == "RAISE_VARARGS":
        return -oparg

    # jump dependant
    if opname == "JUMP_IF_FALSE_OR_POP":
        return -1 if jump else 0
    elif opname == "JUMP_IF_TRUE_OR_POP":
        return 0 if jump else -1
    elif opname == "SETUP_ASYNC_WITH":
        return -1 if jump else 0

    return 0

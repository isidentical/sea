import dis
import types
from collections import defaultdict
from pprint import pprint

from sea import virtuals
from sea.simulator import simulate_ir


def analyze(function):
    instructions = tuple(dis.Bytecode(function))
    virtual_blocks = virtuals.traverse_virtuals(simulate_ir(instructions))

    block_map = {
        virtual_block.name: virtual_block for virtual_block in virtual_blocks
    }
    def_map = defaultdict(set)
    use_map = defaultdict(set)
    elimination_blocks = defaultdict(set)

    for virtual_block in virtual_blocks:
        for call in virtual_block.calls:
            if call.func.opname == "STORE_FAST":
                assert isinstance(name := call.arguments[0], virtuals.Constant)
                def_map[name.value].add(virtual_block.name)
            elif call.func.opname == "LOAD_FAST":
                assert isinstance(name := call.arguments[0], virtuals.Constant)
                use_map[name.value].add(virtual_block.name)

    for name, defined_blocks in def_map.items():
        used_blocks = use_map[name]
        if (
            len(defined_blocks) == 1
            and len(used_blocks) == 1
            and defined_blocks == used_blocks
        ):
            [use_block] = used_blocks
            elimination_blocks[name].add(use_block)
            continue

        elimination_blocks[name].update(used_blocks)

    pprint(def_map)
    pprint(use_map)
    pprint(elimination_blocks)


def find_function(name, consts):
    for const in consts:
        if isinstance(const, types.CodeType) and const.co_name == name:
            return const

    raise ValueError("can't find")


bytecode = compile(
    """
def func():
    a = 1
    if something:
        b, c, d, e = 1, 2, 3, 4
        print(b)
        if blabla:
            print("d: ", d)
        else:
            print(d)
        print(e)
    else:
        c = 2

    print(a)
    return c

""",
    "<temp>",
    "exec",
)

function = find_function("func", bytecode.co_consts)
analyze(function)

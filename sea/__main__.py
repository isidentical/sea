import dis
from argparse import ArgumentParser

from sea.simulator import simulate, simulate_ir
from sea.transform import transform_blocks, transform_calls
from sea.virtuals import traverse_virtuals
from sea.visualize import visualize_as_graph, visualize_as_text


def get_instructions(source_code):
    return tuple(dis.Bytecode(source_code))


def main():
    parser = ArgumentParser()
    parser.add_argument("file", help="source file")
    parser.add_argument("--enable-ir", action="store_true", help="Enable IR")
    parser.add_argument(
        "--show-graph",
        action="store_true",
        help="display calls in a dot-graph",
    )

    options = parser.parse_args()

    with open(options.file) as stream:
        source = stream.read()

    instructions = get_instructions(source)

    if options.enable_ir:
        virtuals = traverse_virtuals(simulate_ir(instructions))
        graph = transform_blocks(virtuals)
    else:
        virtuals = traverse_virtuals(simulate(instructions))
        graph = transform_calls(virtuals)

    if options.show_graph:
        visualize_as_graph(graph)
    else:
        visualize_as_text(virtuals)


if __name__ == "__main__":
    main()

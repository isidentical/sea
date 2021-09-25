from argparse import ArgumentParser

from sea.simulator import simulate_source
from sea.visualize import visualize_as_graph, visualize_as_text


def main():
    parser = ArgumentParser()
    parser.add_argument("file", help="source file")
    parser.add_argument(
        "--show-graph",
        action="store_true",
        help="display calls in a dot-graph",
    )

    options = parser.parse_args()

    with open(options.file) as stream:
        source = stream.read()

    calls = simulate_source(source)
    if options.show_graph:
        visualize_as_graph(calls)
    else:
        visualize_as_text(calls)


if __name__ == "__main__":
    main()

from sea.graph import Graph
from sea.virtuals import Constant


def _patch_edges(graph, nodes):
    # To provide linearity again after making the dependency-dependant
    # analysis, we will patch each instruction which is not connected
    # to anything else to the next instruction we find.

    for node, next_node in zip(nodes, nodes[1:]):
        if len(node._outgoing_edges) == 0:
            graph.add_edge(node, next_node, metadata={"type": "patched"})


def transform_calls(calls, *, graph=None):
    if graph is None:
        graph = Graph()

    top_level_nodes = []

    for call in calls:
        node = graph.add_node(call)
        top_level_nodes.append(node)

        for index, argument in enumerate(call.arguments):
            if isinstance(argument, Constant):
                continue

            argument_node = graph.add_node(argument)
            graph.add_edge(
                argument_node,
                node,
                metadata={"type": "argument", "position": index},
            )

    _patch_edges(graph, top_level_nodes)
    return graph


def transform_blocks(blocks, *, graph=None):
    if graph is None:
        graph = Graph()

    for block in blocks:
        node = graph.add_node(block)
        transform_calls(block.calls, graph=graph)
        graph.add_edge(graph.add_node(block.calls[-1]), node)

        for next_block in block.next_blocks:
            graph.add_edge(
                node,
                graph.add_node(next_block.calls[0]),
                metadata={"type": "flow"},
            )

    return graph

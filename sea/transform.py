from sea.graph import Graph
from sea.ir import is_jump
from sea.virtuals import Constant


def _patch_edges(graph, nodes):
    # To provide linearity again after making the dependency-dependant
    # analysis, we will patch each instruction which is not connected
    # to anything else to the next instruction we find.

    for node, next_node in zip(nodes, nodes[1:]):
        if len(node._outgoing_edges) == 0:
            graph.add_edge(node, next_node, metadata={"type": "patched"})
        if len(next_node._incoming_edges) == 0:
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

        final_call = block.calls[-1]
        for label, next_block in zip(block.labels, block.next_blocks):
            left = graph.add_node(final_call)
            right = next_block.calls[0]

            # If the block's exit is a jump, then try to infer it's target
            # on the next block
            if is_jump(block.calls[-1].func):
                right = (
                    next_block.find_jump_target(final_call.func.argval)
                    or right
                )

            graph.add_edge(
                left,
                graph.add_node(right),
                metadata={"type": "flow", "label": label},
            )

    return graph

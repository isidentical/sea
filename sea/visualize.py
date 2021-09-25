def reduce_graph(board, calls, outgoing_edges):
    # Patch unconnected edges in the instruction graph (this is not
    # a control flow graph, so we do not consider semantical jumps).

    for call, next_call in zip(calls, calls[1:]):
        if call.name in outgoing_edges:
            continue

        board.edge(call.name, next_call.name, arrowhead="none", color="gray")
    return board


def visualize_as_graph(calls):
    import graphviz

    board = graphviz.Digraph()

    outgoing_edges = set()
    for call in calls:
        board.node(call.name, call.as_string())

        for argument in call.arguments:
            board.node(argument.name, argument.as_string())
            board.edge(argument.name, call.name, color="red")
            outgoing_edges.add(argument.as_string())

    reduce_graph(board, calls, outgoing_edges)

    board.render("/tmp/out.gv", view=True)


def visualize_as_text(calls):
    for call in calls:
        print(call.as_string())

from sea.graph import Graph


def visualize_as_graph(calls):
    import graphviz

    graph = Graph.from_calls(calls)
    board = graphviz.Digraph()

    for node in graph.nodes:
        board.node(node.virtual.name, node.virtual.as_string())

    for edge in graph.edges:
        properties = {}
        if edge.metadata["type"] == "argument":
            properties["color"] = "red"
        elif edge.metadata["type"] == "patched":
            properties["arrowhead"] = "none"
            properties["color"] = "gray"

        board.edge(
            edge.source.virtual.name,
            edge.destination.virtual.name,
            **properties,
        )

    board.render("/tmp/out.gv", view=True)


def visualize_as_text(calls):
    for call in calls:
        print(call.as_string())

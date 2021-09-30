from sea.graph import Graph


def visualize_as_graph(graph):
    import graphviz

    board = graphviz.Digraph()

    for node in graph.nodes:
        board.node(node.virtual.name, node.virtual.as_string())

    for edge in graph.edges:
        properties = {}

        edge_type = edge.metadata.get("type")
        if edge_type == "argument":
            properties["color"] = "red"
        elif edge_type == "flow":
            properties["color"] = "green"
        elif edge_type == "patched":
            properties["arrowhead"] = "none"
            properties["color"] = "gray"

        board.edge(
            edge.source.virtual.name,
            edge.destination.virtual.name,
            **properties,
        )

    board.render("/tmp/out.gv", view=True)


def visualize_as_text(virtuals):
    for virtual in virtuals:
        print(virtual.as_string())

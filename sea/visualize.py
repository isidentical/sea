from sea.virtuals import Block


def visualize_as_graph(graph, enable_subgraphs=True):
    import graphviz

    board = graphviz.Digraph()

    for node in graph.nodes:
        if isinstance(node.virtual, Block):
            if not enable_subgraphs:
                continue

            with board.subgraph(
                name=f"cluster_{node.virtual.name}"
            ) as subgraph:
                subgraph.attr(label=node.virtual.name)
                for call in node.virtual.calls:
                    subgraph.node(call.name, call.as_string())

            continue

        board.node(node.virtual.name, node.virtual.as_string())

    for edge in graph.edges:
        properties = {}

        edge_type = edge.metadata.get("type")
        if edge_type == "argument":
            properties["color"] = "chocolate"
        elif edge_type == "patched":
            properties["arrowhead"] = "none"
            properties["color"] = "gray"

        if label := edge.metadata.get("label"):
            if edge_type == "flow":
                if label == "true":
                    properties["color"] = "green"
                elif label == "false":
                    properties["color"] = "red"
            properties["label"] = label

        board.edge(
            edge.source.virtual.name,
            edge.destination.virtual.name,
            **properties,
        )

    board.render("/tmp/out.gv", view=True)


def visualize_as_text(virtuals):
    for virtual in virtuals:
        print(virtual.as_string())

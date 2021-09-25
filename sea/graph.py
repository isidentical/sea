from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from sea.virtuals import Virtual


@dataclass
class Graph:
    _nodes: Dict[Any, Node] = field(default_factory=dict)
    _edges: Dict[Any, Edge] = field(default_factory=dict)

    @classmethod
    def from_calls(cls, calls):
        """Construct a Graph object from top-level calls"""
        graph = cls()
        graph._add_calls(calls)
        return graph

    def _add(self, cls, store, *args, **kwargs):
        # There might be multiple add() calls with the same
        # objects, so for providing some sort of singleton-like
        # interface, each graph item is responsible for generating
        # a hash-like key (not a hash, just some identifier) and this
        # method gets/sets that key in the given store.

        # TODO: maybe offer get_key() as a class-method to optimize
        # out the new-object creation.
        graph_item = cls(*args, **kwargs)
        if graph_item.key not in store:
            store[graph_item.key] = graph_item

        return store[graph_item.key]

    def add_node(self, *args, **kwargs):
        node = self._add(Node, self._nodes, *args, **kwargs)
        return node

    def add_edge(self, *args, **kwargs):
        edge = self._add(Edge, self._edges, *args, **kwargs)

        edge.source._outgoing_edges.append(edge)
        edge.destination._incoming_edges.append(edge)

        return edge

    @property
    def nodes(self):
        return self._nodes.values()

    @property
    def edges(self):
        return self._edges.values()

    def _add_calls(self, calls):
        top_level_nodes = []

        for call in calls:
            node = self.add_node(call)
            top_level_nodes.append(node)

            for index, argument in enumerate(call.arguments):
                argument_node = self.add_node(argument)
                self.add_edge(
                    argument_node,
                    node,
                    metadata={"type": "argument", "position": index},
                )

        self._patch_edges(top_level_nodes)

    def _patch_edges(self, nodes):
        # For every independent statement, if we do not patch
        # edges we will get a new subgraph. To prevent this,
        # we will simply bind each instruction to the next if
        # they do not already have any outgoing edge in the
        # existing graph. Since this is not a control flow graph,
        # this part is relatively easy because we ignore the jumps.

        for node, next_node in zip(nodes, nodes[1:]):
            if len(node._outgoing_edges) == 0:
                self.add_edge(node, next_node, metadata={"type": "patched"})


class GraphItem:
    @property
    def key(self):
        raise NotImplementedError


@dataclass
class Node(GraphItem):
    virtual: Virtual

    _incoming_edges: List[Edge] = field(default_factory=list, repr=False)
    _outgoing_edges: List[Edge] = field(default_factory=list, repr=False)

    @property
    def key(self):
        return self.virtual.name


@dataclass
class Edge:
    source: Node
    destination: Node
    metadata: Dict[Any, Any] = field(default_factory=dict)

    @property
    def key(self):
        return (self.source.key, self.destination.key)

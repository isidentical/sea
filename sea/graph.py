from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sea.virtuals import Virtual


@dataclass
class Graph:
    _nodes: Dict[Any, Node] = field(default_factory=dict)
    _edges: Dict[Any, Edge] = field(default_factory=dict)

    @classmethod
    def from_calls(cls, calls):
        """Construct a Graph object from top-level calls"""
        from sea.transform import transform_calls

        return transform_calls(calls, graph=cls())

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


class GraphItem:
    @property
    def key(self):
        raise NotImplementedError


@dataclass
class Node(GraphItem):
    """A `node` object in the graph space. It proxies the virtual object it holds."""

    virtual: Virtual

    _incoming_edges: List[Edge] = field(default_factory=list, repr=False)
    _outgoing_edges: List[Edge] = field(default_factory=list, repr=False)

    @property
    def key(self):
        return self.virtual.name


@dataclass
class Edge:
    """Represent a vertex between two different `Node`s. It also holds a dictionary to serve
    as a simple way to create labels, or document details about this edge."""

    source: Node
    destination: Node
    metadata: Dict[Any, Any] = field(default_factory=dict)

    @property
    def key(self):
        return (self.source.key, self.destination.key)

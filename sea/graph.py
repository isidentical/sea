from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sea.virtuals import Virtual


@dataclass
class Graph:
    nodes: List[Node]
    edges: List[Edge]


@dataclass
class Node:
    virtual: Virtual


@dataclass
class Edge:
    source: Node
    destination: Node
    metadata: Dict[Any, Any] = field(default_factory=dict)

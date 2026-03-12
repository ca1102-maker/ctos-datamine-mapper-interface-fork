"""Shared data models for the Frederick platform."""

from dataclasses import dataclass, field


@dataclass
class MatchResult:
    code: str = ""
    term: str = ""
    definition: str = ""
    node_type: str = ""
    score: float = 0.0
    source: str = ""  # "exact" | "synonym" | "semantic" | "fuzzy"
    extra: dict = field(default_factory=dict)


@dataclass
class GraphPayload:
    """Nodes + edges for the graph visualization page."""
    nodes: list = field(default_factory=list)
    edges: list = field(default_factory=list)

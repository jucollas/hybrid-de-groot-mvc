from dataclasses import dataclass

@dataclass(frozen=True)
class Edge:
    """Directed edge u -> v with influence I_uv."""

    neighbor: int
    influence: float

    def __iter__(self):
        yield self.neighbor
        yield self.influence


class Node:
    def __init__(self) -> None:
        self._edges: list[Edge] = []

    def add_edge(self, neighbor: int, influence: float) -> None:
        self._edges.append(Edge(neighbor, influence))

    def get_edges(self) -> list[tuple[int, float]]:
        return [tuple(edge) for edge in self._edges]


class Graph:
    """Graph G=(V,E,I) used by the Hybrid DeGroot model.

    External node ids can be any integers. Internally, the graph stores nodes in
    compact indices because that is what the Rust module receives.
    """

    def __init__(self) -> None:
        self._adj: list[Node] = []
        self._id_to_index: dict[int, int] = {}
        self._index_to_id: list[int] = []
        self._opinion: list[float] = []

    def __len__(self) -> int:
        return len(self._index_to_id)

    def add_node(self, id_node: int, opinion: float) -> None:
        if id_node in self._id_to_index:
            raise ValueError(f"Node id {id_node} already exists")
        self._validate_opinion(opinion)

        self._id_to_index[id_node] = len(self._index_to_id)
        self._index_to_id.append(id_node)
        self._adj.append(Node())
        self._opinion.append(float(opinion))

    def add_edge(self, u: int, v: int, influence: float) -> None:
        if u == v:
            raise ValueError("Self-edges are not allowed")
        if u not in self._id_to_index:
            raise ValueError(f"Source node {u} does not exist")
        if v not in self._id_to_index:
            raise ValueError(f"Target node {v} does not exist")
        if not (influence > 0.0):
            raise ValueError(f"Influence must be positive {u} -> {v} |  w : {influence}")

        source = self._id_to_index[u]
        target = self._id_to_index[v]

        for current_target, _ in self._adj[source].get_edges():
            if current_target == target:
                raise ValueError(f"Edge {u} -> {v} already exists")

        incoming = sum(w for _, current_v, w in self.get_edges_indexed() if current_v == target)
        if incoming + influence > 1.0:
            raise ValueError(
                f"Incoming influence for node {v} would be {incoming + influence:.6f}, "
                "but the model requires sum I_uv <= 1"
            )

        self._adj[source].add_edge(target, float(influence))

    def get_nodes(self) -> list[int]:
        return list(self._index_to_id)

    def get_opinions(self) -> list[float]:
        return list(self._opinion)

    def get_opinions_by_id(self) -> dict[int, float]:
        return dict(zip(self._index_to_id, self._opinion))

    def set_opinions(self, opinions: Iterable[float]) -> None:
        new_opinions = [float(x) for x in opinions]
        if len(new_opinions) != len(self):
            raise ValueError("Opinion vector length does not match the number of nodes")
        for value in new_opinions:
            self._validate_opinion(value)
        self._opinion = new_opinions

    def get_edges(self) -> list[tuple[int, int, float]]:
        """Return edges using external node ids: (u, v, I_uv)."""
        edges: list[tuple[int, int, float]] = []
        for source_index, node in enumerate(self._adj):
            source_id = self._index_to_id[source_index]
            for target_index, influence in node.get_edges():
                target_id = self._index_to_id[target_index]
                edges.append((source_id, target_id, influence))
        return edges

    def get_edges_indexed(self) -> list[tuple[int, int, float]]:
        """Return edges using internal indices: (u_index, v_index, I_uv)."""
        edges: list[tuple[int, int, float]] = []
        for source_index, node in enumerate(self._adj):
            for target_index, influence in node.get_edges():
                edges.append((source_index, target_index, influence))
        return edges

    def edge_pair_to_indices(self, edge: tuple[int, int]) -> tuple[int, int]:
        u, v = edge
        if u not in self._id_to_index or v not in self._id_to_index:
            raise ValueError(f"Unknown edge endpoints: {u} -> {v}")
        return self._id_to_index[u], self._id_to_index[v]

    def indices_to_edge_pair(self, edge : tuple[int, int])-> tuple[int, int]:
        u, v = edge
        if u > len(self._index_to_id) or v > len(self._index_to_id):
            raise ValueError(f"Unknown edge endpoints: {u} -> {v}")
        return self._index_to_id[u], self._index_to_id[v]

    def get_adj(self):
        ans = []
        for node in self._adj:
            ans.append(node.get_edges())
        return ans


    @staticmethod
    def _validate_opinion(value: float) -> None:
        if not (0.0 <= float(value) <= 1.0):
            raise ValueError("Opinions must be in the interval [0, 1]")

    def __str__(self) -> str:
        if len(self) == 0:
            return "<Graph empty>"
        lines: list[str] = []
        for node_id, opinion in self.get_opinions_by_id().items():
            outgoing = [(v, w) for u, v, w in self.get_edges() if u == node_id]
            lines.append(f"{node_id} ({opinion:.4f}) -> {outgoing}")
        return "\n".join(lines)

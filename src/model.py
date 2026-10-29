from __future__ import annotations

from .graph import Graph
from .engine import Engine
from .dataloader import DataLoader

from pathlib import Path


class HybridModel:
    """Application model.

    This class owns the graph state and delegates the numerical update to the
    Rust extension built with maturin. If the extension is not installed yet, it
    falls back to the same formula in Python so the interface can still open.
    """

    """
    * Public Function
    """

    def __init__(self) -> None:
        self._graph: Graph = Graph()
        self._tao : float = 0.0
        self._engine : Engine = Engine()
        self._dataloader : DataLoader = DataLoader()

    @classmethod
    def from_file(cls, filename: str | Path) -> "HybridModel":
        model = cls()
        model._graph = model._dataloader.run(filename)
        return model

    def get_tao(self) -> float:
        return self._tao

    def set_tao(self, tao) -> None:
        self._tao = tao
    
    def generate_random_valid_tao(self, seed : int):
        import random
        random.seed(seed)
        opinions = self._graph.get_opinions()
        min_op = min(opinions)
        max_op = max(opinions)
        tao = random.uniform(min_op, max_op)
        self.set_tao(tao)

    def find_consensus_steps(self, eps : float) -> None:
        opinions = self._graph.get_opinions()
        edges_indexed = self._graph.get_edges_indexed()
        adj_graph = self._graph.get_adj()
        return self._engine._compute_steps_consensus_python(opinions, edges_indexed, adj_graph,  self._tao, eps)


    def snapshot(self) -> dict:
        return {
            "nodes": self._graph.get_nodes(),
            "opinions": self._graph.get_opinions_by_id(),
            "edges": self._graph.get_edges(),
            "tao" : self.get_tao(),
        }

    @classmethod
    def demo(cls) -> "HybridModel":
        model = cls()
        nodes = [(1, 0.10), (2, 0.85), (3, 0.45), (4, 0.70), (5, 0.20)]
        for node_id, opinion in nodes:
            model._add_node(node_id, opinion)
        edges = [
            (2, 1, 0.5),
            (1, 2, 0.25),
            (3, 2, 0.20),
            (2, 3, 0.35),
            (4, 3, 0.25),
            (2, 4, 0.30),
            (5, 4, 0.20),
            (4, 5, 0.40),
            (1, 5, 0.10)
        ]
        for u, v, influence in edges:
            model._add_edge(u, v, influence)
        return model

    """
    * Private Function
    """
    
    def _add_node(self, id_node: int, opinion: float) -> None:
        self._graph.add_node(id_node, opinion)

    def _add_edge(self, u: int, v: int, influence: float) -> None:
        self._graph.add_edge(u, v, influence)

    """
        Funciones irrelevantes para el engine, actualizar despues para la visualizacion
    """
    """
    @property
    def get_edges(self) -> list[tuple[int, int, float]]:
        return self._graph.get_edges()

    def _get_nodes(self) -> list[int]:
        return self._graph.get_nodes()
    
    def _get_opinions_by_id(self) -> dict[int, float]:
        return self._graph.get_opinions_by_id()

    """

    

if __name__ == "__main__":
    model = HybridModel.demo()
    print(model.snapshot())
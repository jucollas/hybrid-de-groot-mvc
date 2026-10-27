from __future__ import annotations

from .graph import Graph

from pathlib import Path
from typing import Iterable
import math

EPS = 1e-4

class HybridModel:
    """Application model.

    This class owns the graph state and delegates the numerical update to the
    Rust extension built with maturin. If the extension is not installed yet, it
    falls back to the same formula in Python so the interface can still open.
    """

    def __init__(self) -> None:
        self._graph: Graph = Graph()
        self._enabled_edges: list[tuple[int, int]] = []
        self._time: int = 0

        self._last_backend: str = "not computed yet"

        self._tao : float = 0.0
        self._step_to_consensus : list[list[tuple[int, int, float]]] = []
        self._current_step = 0

    @property
    def time(self) -> int:
        return self._time

    def generate_random_tao(self):
        import random
        opinions = self._graph.get_opinions()
        min_op = min(opinions)
        max_op = max(opinions)
        tao = random.uniform(min_op, max_op)
        self.set_tao(tao)


    def get_len_step_to_consensus(self) -> int:
        return len(self._step_to_consensus)

    @property
    def backend(self) -> str:
        return self._last_backend

    def set_tao(self, tao) -> None:
        self._tao = tao

    def get_tao(self) -> float:
        return self._tao

    def add_node(self, id_node: int, opinion: float) -> None:
        self._graph.add_node(id_node, opinion)

    def add_edge(self, u: int, v: int, influence: float) -> None:
        self._graph.add_edge(u, v, influence)
        self._enabled_edges = [(u, v) for u, v, _ in self._graph.get_edges()]

    def get_edges(self) -> list[tuple[int, int, float]]:
        return self._graph.get_edges()

    def get_nodes(self) -> list[int]:
        return self._graph.get_nodes()

    def get_opinions_by_id(self) -> dict[int, float]:
        return self._graph.get_opinions_by_id()

    def set_enabled_edges(self, edges: Iterable[tuple[int, int]]) -> None:
        valid_edges = {(u, v) for u, v, _ in self._graph.get_edges()}
        selected = []
        for edge in edges:
            if edge not in valid_edges:
                raise ValueError(f"Selected edge {edge} is not part of the graph")
            selected.append(edge)
        self._enabled_edges = selected

    def next_time(self) -> None:
        opinions = self._graph.get_opinions()
        edges_indexed = self._graph.get_edges_indexed()
        enabled_indexed = [self._graph.edge_pair_to_indices(edge) for edge in self._enabled_edges]

        try:
            new_opinions = self._compute_next_opinions_rust(opinions, edges_indexed, enabled_indexed)
            self._last_backend = "Rust / maturin"
        except Exception as exc:
            new_opinions = self._compute_next_opinions_python(opinions, edges_indexed, enabled_indexed)
            self._last_backend = f"Python fallback ({exc.__class__.__name__})"

        self._graph.set_opinions(new_opinions)
        self._time += 1

    def next_time_auto(self):
        opinions = self._graph.get_opinions()
        edges_indexed = self._graph.get_edges_indexed()
        self._enabled_edges = [self._graph.indices_to_edge_pair(edge) for edge in self._step_to_consensus[self._current_step]]
        enabled_indexed = self._step_to_consensus[self._current_step]

        """try:
            new_opinions = self._compute_next_opinions_rust(opinions, edges_indexed, enabled_indexed)
            self._last_backend = "Rust / maturin"
        except Exception as exc:
            new_opinions = self._compute_next_opinions_python(opinions, edges_indexed, enabled_indexed)
            self._last_backend = f"Python fallback ({exc.__class__.__name__})" """

        new_opinions = self._compute_next_opinions_python(opinions, edges_indexed, enabled_indexed)
        self._graph.set_opinions(new_opinions)
        self._time += 1
        self._current_step += 1

    def find_consensus(self) -> None:
        opinions = self._graph.get_opinions()
        edges_indexed = self._graph.get_edges_indexed()
        adj_graph = self._graph.get_adj()
        self._step_to_consensus = self._compute_steps_consensus_python(opinions, edges_indexed, adj_graph,  self._tao)


    def snapshot(self) -> dict:
        return {
            "time": self._time,
            "backend": self._last_backend,
            "nodes": self._graph.get_nodes(),
            "opinions": self._graph.get_opinions_by_id(),
            "edges": self._graph.get_edges(),
            "enabled_edges": list(self._enabled_edges),
            "tao" : self._tao,
        }

    def load_from_file(self, filename: str | Path) -> None:
        path = Path(filename)
        tokens = path.read_text(encoding="utf-8").split()
        if len(tokens) < 2:
            raise ValueError("Input file must start with: n_nodes n_edges")

        self._graph = Graph()
        self._time = 0
        self._last_backend = "not computed yet"

        n_nodes, n_edges = int(tokens[0]), int(tokens[1])
        index = 2

        for _ in range(n_nodes):
            node_id = int(tokens[index])
            opinion = float(tokens[index + 1])
            self._graph.add_node(node_id, opinion)
            index += 2

        for _ in range(n_edges):
            u = int(tokens[index])
            v = int(tokens[index + 1])
            influence = float(tokens[index + 2])
            self._graph.add_edge(u, v, influence)
            index += 3

        self._enabled_edges = [(u, v) for u, v, _ in self._graph.get_edges()]

    @classmethod
    def from_file(cls, filename: str | Path) -> "HybridModel":
        model = cls()
        model.load_from_file(filename)
        return model

    @classmethod
    def demo(cls) -> "HybridModel":
        model = cls()
        for node_id, opinion in [(1, 0.10), (2, 0.85), (3, 0.45), (4, 0.70), (5, 0.20)]:
            model.add_node(node_id, opinion)
        model.add_edge(2, 1, 0.5)
        model.add_edge(1, 2, 0.25)
        model.add_edge(3, 2, 0.20)
        model.add_edge(2, 3, 0.35)
        model.add_edge(4, 3, 0.25)
        model.add_edge(2, 4, 0.30)
        model.add_edge(5, 4, 0.20)
        model.add_edge(4, 5, 0.40)
        model.add_edge(1, 5, 0.10)
        return model

    @staticmethod
    def _compute_next_opinions_rust(
        opinions: list[float],
        edges_indexed: list[tuple[int, int, float]],
        enabled_indexed: list[tuple[int, int]],
    ) -> list[float]:
        import opinion_core  # built by: maturin develop --release

        return opinion_core.next_opinions(opinions, edges_indexed, enabled_indexed)

    @staticmethod
    def _compute_next_opinions_python(
        opinions: list[float],
        edges_indexed: list[tuple[int, int, float]],
        enabled_indexed: list[tuple[int, int]],
    ) -> list[float]:
        selected = set(enabled_indexed)
        next_opinions = opinions.copy()
        incoming_sum = [0.0 for _ in opinions]

        for u, v, influence in edges_indexed:
            if (u, v) not in selected:
                continue
            incoming_sum[v] += influence
            if incoming_sum[v] > 1.0:
                raise ValueError("Selected incoming influence exceeds 1")
            next_opinions[v] += influence * (opinions[u] - opinions[v])

        return [min(1.0, max(0.0, value)) for value in next_opinions]
    
    @staticmethod
    def _find_min_edge(
        edges_indexed: list[tuple[int, int, float]]
    ) -> tuple[int, int, float]:
        ans = None
        for u, v, influence in edges_indexed:
            if ans is None or influence < ans[2]:
                ans = (u, v, influence)
        return ans
    
    @staticmethod
    def _find_node_closest_tao_opinion(
            opinion : list[float],
            tao : float
        ) -> int:
        ans, u = None, 0
        for u in range(len(opinion)):
            if ans is None or abs(tao - opinion[u]) < abs(tao - opinion[ans]):
                ans = u
        return ans

    def _remove_nodes_in_consensus(
            self,
            nodes : set[int],
            opinion : set[float],
            low : float,
            high : float    
        ) -> set[int]:  
        return {
            u for u in nodes
            if not low <= opinion[u] <= high
        }

    def _compute_new_opinion(
            self,
            opinions : list[float],
            enabled_indexed : list[tuple[int, int, float]]    
        ) -> None:
        delta : dict[int, float] = {}        
        for u, v, influence in enabled_indexed:
            delta[v] = (
                delta.get(v, 0.0)
                + influence * (opinions[u] - opinions[v])
            )
        for v, change in delta.items():
            opinions[v] += change

    def _copy_opinion_set_nodes(
            self,
            nodes : set[int],
            edges : list[tuple[int, int, float]],
            opinion : list[float],
            tao : float              
        ) -> list[list[tuple[int, int]]]: 
        ans = []
        low = max(tao - EPS, 0.0)
        high = min(tao + EPS, 1.0)
        nodes = self._remove_nodes_in_consensus(nodes, opinion, low, high)
        edges = [   
            (u, v, infl) 
            for u, v, infl in edges 
            if v in nodes
        ]
        while len(nodes) > 0:
            ans.append(edges)
            self._compute_new_opinion(opinion, edges)
            nodes = self._remove_nodes_in_consensus(nodes, opinion, low, high)
            edges = [   
                (u, v, infl) 
                for u, v, infl in edges 
                if v in nodes
            ]
        return ans 
                
    def _copy_opinion_all(
            self,
            source_node : int ,
            opinions : list[float],
            adj_graph : list[list[tuple[int, float]]],
            tao : float,
        ) -> list[list[tuple[int, int]]]:
        from collections import deque
        visited = [ False for _ in range(len(adj_graph))]
        visited[source_node] = True
        q = deque()
        q.append((source_node, 0))
        cur_nodes, cur_edges = set(), list()
        ans = []
        cur_dist = 0
        while len(q) > 0:
            u, du = q.popleft()
            if du > cur_dist:
                cur_dist = du
                steps = self._copy_opinion_set_nodes(cur_nodes, cur_edges, opinions, tao) 
                ans.extend(steps)
                cur_nodes, cur_edges = set(), list()
                
            for v, influence in adj_graph[u]:
                if not visited[v]:
                    visited[v] = True
                    q.append((v, du + 1))
                    cur_edges.append((u, v, influence))
                    cur_nodes.add(v)

        if len(cur_nodes) > 0:
            steps = self._copy_opinion_set_nodes(cur_nodes, cur_edges, opinions, tao)
            ans.extend(steps)
            cur_nodes, cur_edges = set(), list()

        return ans

    def _copy_opinion_path(
            self,
            path : list[tuple[int, int, float]],
            opinions : list[float],
            LAMBDA : float = EPS,
        ):
        ans = []
        start, _, _ = path[0]
        _, term, _ = path[-1]
        low  = max(opinions[start] - LAMBDA, 0.0)
        high = min(opinions[start] + LAMBDA, 1.0)
        path_simple = [ (u, v) for u, v, _ in path ]
        while not (low <= opinions[term] <= high):
            self._compute_new_opinion(opinions, path)
            ans.append(path_simple)
        return ans

    def _build_node_tao(
            self,
            alpha_edge : tuple[int, int, float],
            opinions : list[float],
            path : list[tuple[int, int, float]],
            tao : float,
            LAMBDA: float,
            timeout: int=100,
        ):
        ans = []
        u, v, influence_u_to_v = alpha_edge
        w, _, influence_w_to_u = path[-1]
        low  = max(tao - LAMBDA, 0.0)
        high = min(tao + LAMBDA, 1.0)
        side_u = opinions[u] > tao
        side_v = opinions[v] > tao
        c = max(1 - influence_u_to_v, 1 - influence_w_to_u, abs( 1 - influence_u_to_v - influence_w_to_u))
        LAMBDA_path = (LAMBDA / math.log(LAMBDA / 2, c)) / 2
        assert(0<LAMBDA_path<=LAMBDA)

        i = 0
        while not(low < opinions[u] < high and low < opinions[v] < high) and i < timeout:
            swap_v = ((opinions[v] + (influence_u_to_v * (opinions[u] - opinions[v]))) > tao) ^ side_v
            swap_u = ((opinions[u] + (influence_w_to_u * (opinions[v] - opinions[u]))) > tao) ^ side_u

            if not (swap_u ^ swap_v):
                if len(path) == 1:
                    temp = opinions[v]
                    opinions[v] += influence_u_to_v * (opinions[u] - opinions[v])
                    opinions[u] += influence_w_to_u * (temp - opinions[u])
                    ans.append([(u, v), (v, u)])
                else:
                    steps_copy_path = self._copy_opinion_path(path[:-1], opinions,LAMBDA_path)
                    ans.extend(steps_copy_path)
                    opinions[v] += influence_u_to_v * (opinions[u] - opinions[v])
                    ans.append([(u, v)])
                    opinions[u] += influence_w_to_u * (opinions[w] - opinions[u])
                    ans.append([(w, u)])
            elif not swap_v:
                opinions[v] += influence_u_to_v * (opinions[u] - opinions[v])
                ans.append([(u, v)])
            elif not swap_u:
                if len(path) > 1:
                    steps_copy_path = self._copy_opinion_path(path[:-1], opinions,LAMBDA_path)
                    ans.extend(steps_copy_path)
                opinions[u] += influence_w_to_u * (opinions[w] - opinions[u])
                ans.append([(w, u)])

            side_u = opinions[u] > tao
            side_v = opinions[v] > tao
            i += 0

        return ans


    @staticmethod
    def _find_path(start, term, G, restrict : set = {}):
        from collections import deque
        n = len(G)
        parent = [ None for _ in range(n)]
        visted = [ False for _ in range(n)]
        visted[start] = True
        q = deque()
        q.append(start)
        found = False
        while len(q) > 0 and not found:
            u = q.popleft()
            if u == term:
                found = True
            else:
                for v, duv in G[u]:
                    if v not in restrict and not visted[v]:
                        q.append(v)
                        visted[v] = True
                        parent[v] = (u, duv)
        path = []
        u = term
        while parent[u] != None:
            p, dist = parent[u]
            path.append((p, u, dist))
            u = p
        path.reverse()

        return path

    def _find_node_maximize_function(self, opinions, search_fun):
        ans = 0
        for u in range(len(opinions)):
            if search_fun(opinions[u]) > search_fun(opinions[ans]):
                ans = u
        return ans

    def _build_alpha_edge(
            self,
            beta : tuple[int, int, float],
            opinions : list[float],
            adj_graph : list[list[tuple[int, float]]],
            tao : float,
        ):
        u, v, _ = beta
        
        if opinions[u] > tao: 
            search_fun = lambda x:-x
        else: 
            search_fun = lambda x:x
            
        omega = self._find_node_maximize_function(opinions, search_fun)
        path = self._find_path(omega, u, adj_graph, {v})
        if path == None:
            path = self._find_path(omega, v, adj_graph, {u})
        steps_copy_path = self._copy_opinion_path(path, opinions, abs(opinions[omega] - tao))
        return steps_copy_path

    def check_all(
            self, 
            tao : float, 
            opinions : list[float]
        ) -> None:
        low  = max(tao - EPS, 0.0)
        high = min(tao + EPS, 1.0)
        
        for u in range(len(opinions)):
            if not low <= opinions[u] <= high:
                raise ValueError(f"{low} <= {opinions[u]} < {high} [{u}] : Not check")

    def _compute_steps_consensus_python(
            self,
            opinions: list[float],
            edges_indexed: list[tuple[int, int, float]],
            adj_graph : list[list[tuple[int, float]]],
            tao : float,
        ) -> list[list[tuple[int, int, float]]]:
        ans = []
        eps_half = EPS / 2

        alpha = self._find_min_edge(edges_indexed)
        if alpha == None: 
            return ans
        
        influence = alpha[2]
        node_tao = self._find_node_closest_tao_opinion(opinions,tao)

        if influence < 1.0:
            min_opinion, max_opinion = min(opinions), max(opinions)
            low =  min_opinion + eps_half
            high = max_opinion - eps_half
            if low <= tao <= high:
                u, v, _ = alpha
                if min(opinions[u], opinions[v]) > tao or max(opinions[u], opinions[v]) < tao:
                    steps_build_alpha_edge = self._build_alpha_edge(alpha, opinions, adj_graph, tao)
                    ans.extend(steps_build_alpha_edge)
                path_v_to_u = self._find_path(v, u, adj_graph)
                steps_build_node_tao = self._build_node_tao(alpha, opinions, path_v_to_u, tao, eps_half)
                ans.extend(steps_build_node_tao)
                node_tao = alpha[0]

        steps_copy_all = self._copy_opinion_all(node_tao, opinions, adj_graph, tao)
        ans.extend(steps_copy_all)

        self.check_all(tao, opinions)
        
        return ans

if __name__ == "__main__":
    model = HybridModel.demo()
    print(model.snapshot())
    model.set_enabled_edges([(1, 2), (2, 3), (4, 5)])
    model.next_time()
    print(model.snapshot())
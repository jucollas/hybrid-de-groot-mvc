from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import math


EPS = 1e-4


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
        if incoming + influence > 1.0 + EPS:
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
        self._step_to_consensus : list[list[tuple[int, int]]] = []
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

    def find_consensus(self):
        opinions = self._graph.get_opinions()
        edges_indexed = self._graph.get_edges_indexed()
        adj_graph = self._graph.get_adj()
        self._step_to_consensus = self._compute_steps_consensus_python(opinions, edges_indexed, adj_graph,  self._tao)
        self._current_step = 0


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
            if incoming_sum[v] > 1.0 + EPS:
                raise ValueError("Selected incoming influence exceeds 1")
            next_opinions[v] += influence * (opinions[u] - opinions[v])

        return [min(1.0, max(0.0, value)) for value in next_opinions]
    @staticmethod
    def _find_min_edge(
        edges_indexed:list[tuple[int,int,float]]
    )->tuple[int,int,float]:
        res=None
        for edge in edges_indexed:
            if(res==None or res[2]>edge[2]):
                res=edge
        return res
    @staticmethod
    def _find_node_with_tao_opinion(
            op : list[float],
            tao : float
        ):
        ans, u = None, 0
        low = max(tao - EPS, 0.0)
        high = min(tao + EPS, 1.0)
        for u in range(len(op)):
            if low <= op[u] <= high and (ans==None or abs(tao-op[u])<abs(tao-op[ans]) ):
                ans = u
        return ans

    def _all_nodes_in_consensus(self, opinions, tao):
        ans = True
        low = max(tao - EPS, 0.0)
        high = min(tao + EPS, 1.0)
        for op in opinions:
            ans = ans and low <= op <= high
        return ans

    def _copy_opinion_all(
            self,
            source_node : int ,
            opinions : list[float],
            edges_indexed : list[tuple[int, int, float]],
            tao : float
        ):
        ans = []
        edges_enables = [ (u, v) for u, v, _ in edges_indexed if v != source_node]
        while not self._all_nodes_in_consensus(opinions, tao):
            opinions = self._compute_next_opinions_python(opinions, edges_indexed, edges_enables)
            ans.append(edges_enables)
        return ans

    def _copy_opinion_path(
            self,
            path : list[tuple[int, int, float]],
            opinions : list[float],
            LAMBDA:float=EPS,
        ):
        ans = []
        start, _, _ = path[0]
        _, term, _ = path[-1]
        low  = max(opinions[start] - LAMBDA, 0.0)
        high = min(opinions[start] + LAMBDA, 1.0)
        path_simple = [ (u, v) for u, v, _ in path ]
        #print(" SI entre a copiar")
        op = opinions.copy()

        while not (low <= op[term] <= high):
            next_opinions = op.copy()
            for u, v, influence in path:
            #incoming_sum[v] += influence
            #if incoming_sum[v] > 1.0 + EPS:
                #raise ValueError("Selected incoming influence exceeds 1")
                next_opinions[v] += influence * (op[u] - op[v])
            next_opinions = [min(1.0, max(0.0, value)) for value in next_opinions]
            op = next_opinions
            ans.append(path_simple)
        for i in range(len(opinions)):
            opinions[i] = op[i]
        #print(opinions)
        return ans



    def _build_node_tao(
            self,
            alpha_edge : tuple[int, int, float],
            opinions : list[float],
            path : list[tuple[int, int, float]],
            tao : float,
            LAMBDA:float,
            timeout:int=100,
        ):
        ans = []
        u, v, influence_u_to_v = alpha_edge
        w, _, influence_w_to_u = path[-1]
        low  = max(tao - LAMBDA, 0.0)
        high = min(tao + LAMBDA, 1.0)
        side_u = opinions[u] > tao
        side_v = opinions[v] > tao
        c=max(1-influence_u_to_v,1-influence_w_to_u,abs(1-influence_u_to_v-influence_w_to_u))
        LAMBDA_path=(LAMBDA/math.log(LAMBDA/2,c))/2
        assert(0<LAMBDA_path<=LAMBDA)
        i = 0
        while not(low < opinions[u] < high and low < opinions[v] < high) and i < timeout:
            #print(opinions[u])
            #print(opinions[v])
            #print("Lado de u", side_u)
            #print("lado de v", side_v)
            swap_v = ((opinions[v] + (influence_u_to_v * (opinions[u] - opinions[v]))) > tao) ^ side_v
            swap_u = ((opinions[u] + (influence_w_to_u * (opinions[v] - opinions[u]))) > tao) ^ side_u
            tmp_u = opinions[u] + (influence_w_to_u * (opinions[v] - opinions[u]))
            tmp_v = opinions[v] + (influence_u_to_v * (opinions[u] - opinions[v]))

            #print("valor de u si se activa la arista :", tmp_u)
            #print("valor de v si se activa la arista :", tmp_v)

            #print("U cambia de lado", swap_u)
            #print("V cambia de lado", swap_v)

            #print(swap_u, swap_v)
            if not (swap_u ^ swap_v):
                if len(path) == 1:
                    #print("Activo ambos")
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
                #print("Activo u -> v")
                # activo la arista de u -> v
                opinions[v] += influence_u_to_v * (opinions[u] - opinions[v])
                ans.append([(u, v)])
            elif not swap_u:
                #print("Activo v -> u")
                if len(path) > 1:
                    steps_copy_path = self._copy_opinion_path(path[:-1], opinions,LAMBDA_path)
                    ans.extend(steps_copy_path)
                #print("sali")
                opinions[u] += influence_w_to_u * (opinions[w] - opinions[u])
                ans.append([(w, u)])

            side_u = opinions[u] > tao
            side_v = opinions[v] > tao
            i += 0
            #print("="*20)

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

    @staticmethod
    def _get_edges_no_puppet(edges_indexed):
        return [(u, v, duv) for u, v, duv in edges_indexed if duv < 1.0 ]


    @staticmethod
    def _find_edge_alpha(
            edges_no_puppet : list[tuple[int, int, float]],
            opinion : list[float],
            tao : float
        ):
        index = 0
        ans = None
        while index < len(edges_no_puppet) and ans == None:
            u, v, duv = edges_no_puppet[index]
            op_max, op_min = opinion[u], opinion[v]
            if op_max < op_min: op_max, op_min = op_min, op_max
            if op_min < tao < op_max:
                ans = (u, v, duv)
            index += 1
        return ans


    def _find_node_function_opinion(self, opinions, search_fun):
        u = 0
        ans = None
        while u < len(opinions) and ans == None:
            if search_fun(opinions[u]): ans = u
            u += 1
        return ans
    def _find_node_maximize_function(self,opinions,search_fun):
        ans=None
        for u in range(len(opinions)):
            if(ans==None or search_fun(opinions[u])>search_fun(opinions[ans])):
                ans=u
        return ans

    def _build_alpha_edge(
            self,
            beta : tuple[int, int, float],
            opinions : list[float],
            adj_graph : list[list[tuple[int, float]]],
            tao : float,
        ):
        u, v, _ = beta
        #print(u, v)
        #search_fun = lambda x : x < tao if opinions[u] > tao else lambda x : x > tao
        #if opinions[u] > tao: search_fun = lambda x : x < tao
        #else: search_fun = lambda x : x > tao
        #omega = self._find_node_function_opinion(opinions, search_fun)
        
        if(opinions[u]>tao):search_fun=lambda x:-x
        else: search_fun=lambda x:x
        omega=self._find_node_maximize_function(opinions,search_fun)

        #print(omega,opinions[omega])
        path = self._find_path(omega, u, adj_graph, {v})
        if path == None:
            path = self._find_path(omega, v, adj_graph, {u})
        #print(path)
        steps_copy_path = self._copy_opinion_path(path, opinions, abs(opinions[omega]-tao))
        #print(opinions)
        #print(steps_copy_path)
        #print(opinions[0])

        return steps_copy_path

    def _compute_steps_consensus_python(
            self,
            opinions: list[float],
            edges_indexed: list[tuple[int, int, float]],
            adj_graph : list[list[tuple[int, float]]],
            tao : float,
        ):
        ans = []
        alpha=self._find_min_edge(edges_indexed)
        if(alpha==None):return ans # no edges in the graph        
        node_tao=None
        if(alpha[2]==1): # puppet graph case
            node_tao=self._find_node_with_tao_opinion(opinions,tao)
        else:
            assert(0<alpha[2]<1)
            min_opinion,max_opinion=min(opinions),max(opinions)
            if(min_opinion+EPS/2<=tao<=max_opinion-EPS/2):
                if(min(opinions[alpha[0]],opinions[alpha[1]])>tao or max(opinions[alpha[0]],opinions[alpha[1]])<tao):
                    steps_build_alpha_edge=self._build_alpha_edge(alpha,opinions,adj_graph,tao)
                    ans.extend(steps_build_alpha_edge)
                u, v, _ = alpha
                #print(alpha)
                #print(opinions[u], opinions[v])
                path_v_to_u = self._find_path(v, u, adj_graph)
                steps_build_node_tao = self._build_node_tao(alpha, opinions, path_v_to_u, tao,EPS/2)
                ans.extend(steps_build_node_tao)
                node_tao = alpha[0]
            else:
                node_tao=self._find_node_with_tao_opinion(opinions,tao)
        if(node_tao!=None):
            steps_copy_all = self._copy_opinion_all(node_tao, opinions, edges_indexed, tao)
            ans.extend(steps_copy_all)


                
        """
        node_tao = self._find_node_with_tao_opinion(opinions, tao)
        if node_tao == None:
            edges_no_puppet = self._get_edges_no_puppet(edges_indexed)
            if len(edges_no_puppet) != 0 and min(opinions) <= tao <= max(opinions):
                alpha = self._find_edge_alpha(edges_no_puppet, opinions, tao)
                if alpha == None:
                    beta = edges_no_puppet[0]
                    steps_build_alpha_edge = self._build_alpha_edge(beta, opinions, adj_graph, tao)
                    ans.extend(steps_build_alpha_edge)
                    alpha = beta
                u, v, _ = alpha
                #print(alpha)
                #print(opinions[u], opinions[v])
                path_v_to_u = self._find_path(v, u, adj_graph)
                steps_build_node_tao = self._build_node_tao(alpha, opinions, path_v_to_u, tao)
                ans.extend(steps_build_node_tao)
                node_tao = alpha[0]
        if node_tao != None:
            steps_copy_all = self._copy_opinion_all(node_tao, opinions, edges_indexed, tao)
            ans.extend(steps_copy_all)"""
        return ans

if __name__ == "__main__":
    model = HybridModel.demo()
    print(model.snapshot())
    model.set_enabled_edges([(1, 2), (2, 3), (4, 5)])
    model.next_time()
    print(model.snapshot())
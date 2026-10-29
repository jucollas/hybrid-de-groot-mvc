import math

from collections import deque


class Engine:
    
    def __init__(self):
        pass

    @staticmethod
    def _get_low_and_high(
        target : float, 
        eps : float,
    ) -> tuple[float, float]:
        low = max(target - eps, 0.0)
        high = min(target + eps, 1.0)
        return low, high 
    
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
    def _find_node_tao_opinion(
        self, 
        opinion : list[float],
        tao : float,
        eps : float
    ) -> int:
        ans = None
        low, high = self._get_low_and_high(tao, eps)
        for u in range(len(opinion)):
            if ans is None and low <= opinion[u] <= high:
                ans = u
        return ans

    @staticmethod
    def _remove_nodes_in_consensus(
        edges : list[tuple[int, int, float]],
        opinion : set[float],
        low : float,
        high : float    
    ) -> set[int]:  
        return [
            (u, v, influence) for u, v, influence in edges
            if not low <= opinion[v] <= high
        ]

    @staticmethod
    def _compute_new_opinion(
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
        edges : list[tuple[int, int, float]],
        opinion : list[float],
        tao : float,
        eps : float              
    ) -> list[list[tuple[int, int]]]: 
        ans = []
        low, high = self._get_low_and_high(tao, eps)
        edges = self._remove_nodes_in_consensus(edges, opinion, low, high)
        while len(edges) > 0:
            ans.append(edges)
            self._compute_new_opinion(opinion, edges)
            edges = self._remove_nodes_in_consensus(edges, opinion, low, high)
        return ans 

    @staticmethod
    def _get_bfs_levels(
        s : int,
        G : list[list[tuple[int, float]]]        
    ) -> list[list[tuple[int, int, float]]]:
        visited = [ False ] * len(G)
        visited[s] = True
        q = deque()
        q.append((s, 0, None))
        ans = [[]]
        while len(q) > 0:
            u, du, edge = q.popleft()
            if len(ans) - 1 < du: ans.append([])
            ans[du].append(edge)
            for v, influence in G[u]:
                if not visited[v]:
                    visited[v] = True
                    q.append((v, du + 1, (u, v, influence)))
        return ans
        
                
    def _copy_opinion_all(
        self,
        source_node : int ,
        opinions : list[float],
        adj_graph : list[list[tuple[int, float]]],
        tao : float,
        eps : float
    ) -> list[list[tuple[int, int]]]:
        ans = []        
        levels = self._get_bfs_levels(source_node, adj_graph)
        print("levels", levels[:3])
        gama = eps / len(levels)
        for i in range(1, len(levels)):
            steps = self._copy_opinion_set_nodes(levels[i], opinions, tao, eps)
            print(opinions[:10])
            ans.append(steps)
        return ans

    def _copy_opinion_path(
        self,
        path : list[tuple[int, int, float]],
        opinions : list[float],
        eps : float,
    ) -> list[list[tuple[int, int, float]]]:
        ans = []
        start, _, _ = path[0]
        _, term, _ = path[-1]
        low, high = self._get_low_and_high(opinions[start], eps)
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
        eps : float,
        timeout: int = 100,
    ) -> list[list[tuple[int, int, float]]]:
        ans = []
        u, v, influence_u_to_v = alpha_edge
        w, _, influence_w_to_u = path[-1]
        low, high = self._get_low_and_high(tao, eps)
        side_u = opinions[u] > tao
        side_v = opinions[v] > tao
        c = max(1 - influence_u_to_v, 1 - influence_w_to_u, abs( 1 - influence_u_to_v - influence_w_to_u))
        lambda_path = (eps / math.log(eps / 2, c)) / 2
        assert(0 < lambda_path <= eps)

        i = 0
        while not (low < opinions[u] < high and low < opinions[v] < high) and i < timeout:
            swap_v = ((opinions[v] + (influence_u_to_v * (opinions[u] - opinions[v]))) > tao) ^ side_v
            swap_u = ((opinions[u] + (influence_w_to_u * (opinions[v] - opinions[u]))) > tao) ^ side_u
            if not (swap_u ^ swap_v):
                if len(path) == 1:
                    temp = opinions[v]
                    opinions[v] += influence_u_to_v * (opinions[u] - opinions[v])
                    opinions[u] += influence_w_to_u * (temp - opinions[u])
                    ans.append([(u, v), (v, u)])
                else:
                    steps_copy_path = self._copy_opinion_path(path[:-1], opinions, lambda_path)
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
                    steps_copy_path = self._copy_opinion_path(path[:-1], opinions, lambda_path)
                    ans.extend(steps_copy_path)
                opinions[u] += influence_w_to_u * (opinions[w] - opinions[u])
                ans.append([(w, u)])
            side_u = opinions[u] > tao
            side_v = opinions[v] > tao
            i += 0
        return ans


    @staticmethod
    def _find_path(
        start : int, 
        term : int, 
        G : list[list[tuple[int, float]]], 
        restrict : set[int] = set()
    ) -> list[tuple[int, int, float]]:
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

    def _find_node_maximize_function(
        self, 
        opinions : list[float], 
        search_fun : function[float, float]
    ) -> int:
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
        eps : float
    ) -> list[list[tuple[int, int, float]]] :
        u, v, _ = beta

        search_fun = lambda x:x
        if opinions[u] > tao: 
            search_fun = lambda x:-x
            
        omega = self._find_node_maximize_function(opinions, search_fun)
        path = self._find_path(omega, u, adj_graph, {v})
        if path == None:
            path = self._find_path(omega, v, adj_graph, {u})
        steps_copy_path = self._copy_opinion_path(path, opinions, abs(opinions[omega] - tao))
        return steps_copy_path

    def _check_all(
        self, 
        opinions : list[float],
        tao : float, 
        eps : float, 
    ) -> None:
        low, high = self._get_low_and_high(tao, eps)
        for u in range(len(opinions)):
            if not low <= opinions[u] <= high:
                raise ValueError(f"{low} <= {opinions[u]} < {high} [{u}] : Not check")

    def _compute_steps_consensus_python(
        self,
        opinions: list[float],
        edges_indexed: list[tuple[int, int, float]],
        adj_graph : list[list[tuple[int, float]]],
        tao : float,
        eps : float
    ) -> list[list[tuple[int, int, float]]]:
        ans = None
        node_tao = None
        steps_to_consensus = []
        eps_half = eps / 2
        omega = self._find_min_edge(edges_indexed)
        influence = omega[2]
        if influence >= 1.0:
            node_tao = self._find_node_tao_opinion(opinions, tao, eps)
        else:
            alpha = omega
            low =  max(min(opinions) - eps_half, 0.0)
            high = min(max(opinions) + eps_half, 1.0)
            if low <= tao <= high:
                u, v, _ = alpha
                alpha_max = max(opinions[u], opinions[v])
                alpha_min = min(opinions[u], opinions[v])
                if alpha_min > tao or alpha_max < tao:
                    steps_build_alpha_edge = self._build_alpha_edge(alpha, opinions, adj_graph, tao, eps)
                    steps_to_consensus.extend(steps_build_alpha_edge)

                path_v_to_u = self._find_path(v, u, adj_graph)
                steps_build_node_tao = self._build_node_tao(alpha, opinions, path_v_to_u, tao, eps_half)
                steps_to_consensus.extend(steps_build_node_tao)
                node_tao = alpha[0]

        if not node_tao is None:
            print("tao", node_tao)
            steps_copy_all = self._copy_opinion_all(node_tao, opinions, adj_graph, tao, eps)
            steps_to_consensus.extend(steps_copy_all)
            ans = steps_to_consensus
            self._check_all(opinions, tao, eps)
        return ans

        """@staticmethod
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
        
                return [min(1.0, max(0.0, value)) for value in next_opinions]"""
from __future__ import annotations
from collections.abc import Callable
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
        low = max(target - eps, 0.0-1e-12)
        high = min(target + eps, 1.0+1e-12)
        return low, high 
    
    @staticmethod
    def _find_min_edge(
        edges_indexed: list[tuple[int, int, float]]
    ) -> tuple[int, int, float]:
        """
        Receives edges as [(u,v,w),...] where $u-> v$ is and edge with
            weight/influence $w in[0,1]$
        Works in time O(len(edges_indexed))
        """
        ans = None
        for u, v, influence in edges_indexed:
            if ans is None or influence < ans[2]:
                ans = (u, v, influence)
        return ans
    
    def _find_node_tao_opinion(
        self, 
        opinion : list[float],
        tao : float,
        eps : float
    ) -> int:
        """
        Finds a node with opinion $|opinion[ans]-tao|<eps$. In case many such nodes exists
            returns the one with the closest opinion to $tao$. If none exists then None is returned
        Works in time O(len(opinion))
        """
        ans = None
        low, high = self._get_low_and_high(tao, eps)
        for u in range(len(opinion)):
            if low < opinion[u] < high and ( ans is None or abs(tao-opinion[u])<abs(tao-opinion[ans]) ):
                ans = u
        return ans

    @staticmethod
    def _compute_new_opinion(
        opinions : list[float],
        enabled_indexed : list[tuple[int, int, float]]    
    ) -> None:
        """
        Computes a time step in-situ on the opinion state 'opinions'. The edges activated are
            to be found in 'enabled_indexed' as [(u,v,w),...] representing an edge $u-> v$
            with weight/influence w.
        Works in time O(len(enabled_indexed))
        """
        delta : dict[int, float] = {}        
        for u, v, influence in enabled_indexed:
            delta[v] = (
                delta.get(v, 0.0)
                + influence * (opinions[u] - opinions[v])
            )
        for v, change in delta.items():
            opinions[v] += change
    
    @staticmethod
    def _remove_nodes_in_consensus(
        edges : list[tuple[int, int, float]],
        opinion : list[float],
        eps : float 
    ) -> list[tuple[int, int, float]] :  
        return [
            (u, v, influence) for u, v, influence in edges
            if not opinion[u]-eps < opinion[v] < opinion[u]+eps
        ]

    def _copy_opinion_set_nodes(
        self,
        edges : list[tuple[int, int, float]],
        opinion : list[float],
        eps : float              
    ) -> list[list[tuple[int, int,int]]]: 
        """
        Clones the opinions through all edges in 'edges', represented as [(u,v,w),...] 
            where each edge is $u-> v$ with weight/influence w.
        The opinions are cloned to a ball of radius $eps$ from their 'parent'
        """
        ans = []
        edges = self._remove_nodes_in_consensus(edges, opinion, eps )
        while len(edges) > 0:
            ans.append(edges)
            self._compute_new_opinion(opinion, edges)
            edges = self._remove_nodes_in_consensus(edges, opinion, eps )
        return ans 

    @staticmethod
    def _get_bfs_levels(
        s : int,
        G : list[list[tuple[int, float]]]        
    ) -> list[list[tuple[int, int, float]]]:
        """
        Does a BFS in the graph 'G' with source 's'. in 
            ans[l+1]=[(u,v,w),...] where $u$ is a node of level l
            in the BFS tree, $v$ is a node of level l+1 in the BFS
            tree and $(u,v) in E$ is and edge with weight/influence
            w.
        """
        visited = [ False ] * len(G)
        visited[s] = True
        q = deque()
        q.append((s, 0, None))
        ans = [[]]
        while len(q) > 0:
            u, du, edge = q.popleft()
            if len(ans) - 1 < du: ans.append([])
            if edge is not None: ans[du].append(edge)
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
        eps : float
    ) -> list[list[tuple[int, int,int]]]:
        """
        Builds a BFS tree rooted at 'source_node'. Then clones the opinion of node
            'source_node' to all reachable nodes with precision 'eps' from the opinion
            of 'source_node'
        """
        assert(eps>0),"Error: _copy_opinion_all got eps=%f"%(eps)
        ans = []        
        levels = self._get_bfs_levels(source_node, adj_graph)
        #print("levels", levels[:3])
        gama = eps / len(levels)
        for i in range(1, len(levels)):
            steps = self._copy_opinion_set_nodes(levels[i], opinions, gama)
            #print(opinions[:10])
            ans.extend(steps)
        return ans

    def _copy_opinion_path(
        self,
        path : list[tuple[int, int, float]],
        opinions : list[float],
        eps : float,
    ) -> list[list[tuple[int, int, float]]]:
        """
        Clones the opinion through the path of edges in 'path'
            with precision eps. It can be proven that this 
            procedure works in time $O(n log_{1-minedge}(eps/n))$ 
            for $n=len(opinions)$. 
        Notice that it only makes sure that the last node in the path
            is at most at distance $eps$.
        """
        ans = []
        start, _, _ = path[0]
        _, term, _ = path[-1]
        low, high = self._get_low_and_high(opinions[start], eps)
        while not (low < opinions[term] < high):
            self._compute_new_opinion(opinions, path)
            ans.append(path)
        return ans

    def _build_node_tao(
        self,
        alpha_edge : tuple[int, int, float],
        opinions : list[float],
        path : list[tuple[int, int, float]],
        tao : float,
        eps : float,
        timeout: int = 10**5,
    ) -> list[list[tuple[int, int, float]]]:
        """
        This is the equivalent of the Two Agent Generation lemma. It assumes that 
            min(opinions[u],opinions[v])<=tao<=max(opinions[u],opinions[v])

        Notice it ends whenever $u$ or $v$ reaches the objective, thus we dont
            mantain the same invariant as the proof at the end. Furthermore,
            the operation is decided withouth calculating $mu(x)_u$ as we get that
            assuming there is no path allows us to describe it at distance 'lambda_path'
            (by 'self._copy_opinion_path'). If we were to get the side of $mu(x)_u$ wrong
            it's because we have arrived to our objective.
        """
        ans = []
        u, v, influence_u_to_v = alpha_edge
        w, _, influence_w_to_u = path[-1]
        low, high = self._get_low_and_high(tao, eps)
        side_u = opinions[u] > tao
        side_v = opinions[v] > tao
        c = max(1 - influence_u_to_v, 1 - influence_w_to_u, abs( 1 - influence_u_to_v - influence_w_to_u))
        lambda_path = (eps / (math.log(eps / 2, c) + 1 ) ) / 2
        assert(0 < lambda_path <= eps)

        i = 0
        while not (low < opinions[u] < high or low < opinions[v] < high) and i < timeout:
            swap_v = ((opinions[v] + (influence_u_to_v * (opinions[u] - opinions[v]))) > tao) ^ side_v
            swap_u = ((opinions[u] + (influence_w_to_u * (opinions[v] - opinions[u]))) > tao) ^ side_u
            # swap_h is 1 if h changed sides
            if not (swap_u ^ swap_v):# activate both edges as either both or none changed sides
                if len(path) == 1:
                    temp = opinions[v]
                    opinions[v] += influence_u_to_v * (opinions[u] - opinions[v])
                    opinions[u] += influence_w_to_u * (   temp     - opinions[u])
                    ans.append([(u, v,influence_u_to_v), (v, u,influence_w_to_u)])
                else:
                    steps_copy_path = self._copy_opinion_path(path[:-1], opinions, lambda_path)
                    ans.extend(steps_copy_path)
                    opinions[v] += influence_u_to_v * (opinions[u] - opinions[v])
                    ans.append([(u, v,influence_u_to_v)])
                    opinions[u] += influence_w_to_u * (opinions[w] - opinions[u])
                    ans.append([(w, u,influence_w_to_u)])
            elif not swap_v: # it is safe to keep u and change v
                opinions[v] += influence_u_to_v * (opinions[u] - opinions[v])
                ans.append([(u, v,influence_u_to_v)])
            elif not swap_u: # it is safe to keep v and change u
                if len(path) > 1:
                    steps_copy_path = self._copy_opinion_path(path[:-1], opinions, lambda_path)
                    ans.extend(steps_copy_path)
                opinions[u] += influence_w_to_u * (opinions[w] - opinions[u])
                ans.append([(w, u,influence_w_to_u)])
            side_u = opinions[u] > tao
            side_v = opinions[v] > tao
            i += 1
        if not (low < opinions[u] < high or low < opinions[v] < high): assert(False)
        return ans


    @staticmethod
    def _find_path(
        start : int, 
        term : int, 
        G : list[list[tuple[int, float]]], 
        restrict : set[int] = set()
    ) -> list[tuple[int, int, float]]:
        """
        Finds a $start-> term$ path in $G$ with edges restricted in 'restrict'
        """
        n = len(G)
        parent = [ None for _ in range(n)]
        visited = [ False for _ in range(n)]
        visited[start] = True
        q = deque()
        q.append(start)
        found = False
        while len(q) > 0 and not found:
            u = q.popleft()
            if u == term:
                found = True
            else:
                for v, duv in G[u]:
                    if v not in restrict and not visited[v]:
                        q.append(v)
                        visited[v] = True
                        parent[v] = (u, duv)
        if not found: return None
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
        search_fun : Callable[[float], float]
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
        tao : float
    ) -> list[list[tuple[int, int, float]]] :
        """
        We have isolated an edge 'beta'. We want to ensure that
            min(opinions[u],opinions[v])<=tao<=max(opinions[u],opinions[v])
        """
        u, v, _ = beta

        search_fun = lambda x:x
        if opinions[u] > tao: 
            search_fun = lambda x:-x
            
        omega = self._find_node_maximize_function(opinions, search_fun)
        path = self._find_path(omega, u, adj_graph, {v})
        if path is None:
            path = self._find_path(omega, v, adj_graph, {u})
        steps_copy_path = self._copy_opinion_path(path, opinions, abs(opinions[omega] - tao))
        return steps_copy_path

    def _check_all(
        self, 
        opinions : list[float],
        tao : float, 
        eps : float, 
    ) -> None:
        """
        Checks wether $eps$-consensus at opinion $tao$ was reached. Raises 
            ValueError in case it isn't
        """
        low, high = self._get_low_and_high(tao, eps)
        for u in range(len(opinions)):
            if not low < opinions[u] < high:
                raise ValueError(f"{low} < {opinions[u]} < {high} [{u}] : Not check")

    def _compute_steps_consensus_python(
        self,
        opinions: list[float],
        edges_indexed: list[tuple[int, int, float]],
        adj_graph : list[list[tuple[int, float]]],
        tao : float,
        eps : float
    ) -> list[list[tuple[int, int, float]]]:
        """
        Given an opinion state 'opinions', $tao,eps in[0,1]$, and a graph
            represented by its edges 'edges_indexed' as [(u,v,w),...] representing
            $u-> v$ with weight/influence w and it's adjacency graph 'adj_graph'
            where adj_graph[u]=[(v,w),...] representing edges $u-> v$ with weight/
            influence w.
        We compute a finite communication schedule that achieves $eps$-consensus
            at $tao$. It is represented by ans[t]=[(u,v,w),...] where the transition at
            time t are the edges (u,v,w) in ans[t].
        In case there exists no finite communication schedule, None is returned.
        Notice that it only works for strongly connected graphs. Furthermore, notice that
            it modifies 'opinions' in-situ.
        """
        ans = None
        node_tao = None
        steps_to_consensus = []
        eps_half = eps / 2
        omega = self._find_min_edge(edges_indexed)
        if omega is None or omega[2] >= 1.0: # puppet-graph
            node_tao = self._find_node_tao_opinion(opinions, tao, eps)
        else: # non-puppet-graph
            alpha = omega
            minopi,maxopi=min(opinions),max(opinions)
            if minopi + eps_half <= tao <= maxopi - eps_half: 
                u, v, _ = alpha # 2 node game
                alpha_max = max(opinions[u], opinions[v])
                alpha_min = min(opinions[u], opinions[v])
                if alpha_min > tao or alpha_max < tao:
                    steps_build_alpha_edge = self._build_alpha_edge(alpha, opinions, adj_graph, tao )
                    steps_to_consensus.extend(steps_build_alpha_edge)

                path_v_to_u = self._find_path(v, u, adj_graph)
                steps_build_node_tao = self._build_node_tao(alpha, opinions, path_v_to_u, tao, eps_half)
                steps_to_consensus.extend(steps_build_node_tao)
                node_tao = alpha[0] if abs(opinions[alpha[0]]-tao)<=abs(opinions[alpha[1]]-tao) else alpha[1]
            else: # cloning from a single node
                node_tao = self._find_node_tao_opinion(opinions, tao, eps)
        if not node_tao is None:
            #print("tao", node_tao)
            steps_copy_all = self._copy_opinion_all(node_tao, opinions, adj_graph, 
                    min(tao+eps-opinions[node_tao],opinions[node_tao]-(tao-eps)) )
            steps_to_consensus.extend(steps_copy_all)
            ans = steps_to_consensus
            self._check_all(opinions, tao, eps)
        return ans

        """@staticmethod # unused rust integration
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
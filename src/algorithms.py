class TarjanSCC:
  def __init__(self, graph: list[list[int]]):
    self.graph = graph
    self.time = 0
    self.stack = []
    self.inStack = [False for i in  range(len(graph))]
    self.sccInd = [-1 for _ in range(len(graph))]
    self.visited = [-1 for _ in range(len(graph))]
    self.sccs = []

  def _dfs(self, v):
    self.time += 1
    self.visited[v] = self.sccInd[v] = self.time
    self.stack.append(v)
    self.inStack[v] = True

    for w in self.graph[v]:
      if self.visited[w] == -1:
        self._dfs(w)
        self.sccInd[v] = min(self.sccInd[v], self.sccInd[w])
      elif self.inStack[w]:
        self.sccInd[v] = min(self.sccInd[v], self.sccInd[w])

    if self.sccInd[v] == self.visited[v]:
      scc = []
      while self.stack[-1] != v:
        u = self.stack.pop()
        self.inStack[u] = False
        scc.append(u)
      self.inStack[self.stack.pop()] = False
      scc.append(v)
      self.sccs.append(scc)

  def find_sccs(self):
    for v in range(len(self.graph)):
      if self.visited[v] == -1:
        self._dfs(v)
    return self.sccs


if __name__ == "__main__":
    graph = [
        [1],
        [2],
        [0, 3],
        [4],
        [5],
        [],
    ]

    tarjan = TarjanSCC(graph)
    sccs = tarjan.find_sccs()
    print("Strongly Connected Components:")
    for scc in sccs:
        print(scc)

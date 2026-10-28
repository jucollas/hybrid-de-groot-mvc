from pathlib import Path
from .graph import Graph

class DataLoader:
  def __init__(self):
      pass

  @staticmethod
  def run(filename : str | Path) -> Graph:
      path = Path(filename)
      tokens = path.read_text(encoding="utf-8").split()
      if len(tokens) < 2:
          raise ValueError("Input file must start with: n_nodes n_edges")

      ans = Graph()

      n_nodes, n_edges = int(tokens[0]), int(tokens[1])
      index = 2

      for _ in range(n_nodes):
          node_id = int(tokens[index])
          opinion = float(tokens[index + 1])
          ans.add_node(node_id, opinion)
          index += 2

      for _ in range(n_edges):
          u = int(tokens[index])
          v = int(tokens[index + 1])
          influence = float(tokens[index + 2])
          ans.add_edge(u, v, influence)
          index += 3

      return ans
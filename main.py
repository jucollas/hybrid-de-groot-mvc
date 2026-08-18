from __future__ import annotations

import argparse
from pathlib import Path

from src.controller import GraphController
from src.model import HybridModel
from src.view import GraphView


def build_model(input_file: str | None) -> HybridModel:
    if input_file is not None:
        return HybridModel.from_file(input_file)

    default_file = Path(__file__).with_name("sample_graph.txt")
    if default_file.exists():
        return HybridModel.from_file(default_file)

    return HybridModel.demo()


def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid DeGroot opinion-network simulator")
    parser.add_argument("--file", help="Path to a graph file", default=None)
    args = parser.parse_args()

    model = build_model(args.file)
    view = GraphView()
    controller = GraphController(view, model)
    controller.run()


if __name__ == "__main__":
    main()

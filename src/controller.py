from __future__ import annotations

import PySimpleGUI as sg

from .model import HybridModel
from .view import GraphView


class GraphController:
    """Controller: translates GUI events into model operations."""

    def __init__(self, view: GraphView, model: HybridModel) -> None:
        self._view = view
        self._model = model

    def run(self) -> None:
        self._view.update(self._model.snapshot())

        while True:
            event, values = self._view.read_event()

            if event in (sg.WIN_CLOSED, "Exit"):
                break

            try:
                if event == "-SELECT_ALL-":
                    self._model.set_enabled_edges([(u, v) for u, v, _ in self._model.get_edges()])
                    self._view.update(self._model.snapshot())

                elif event == "-CLEAR_EDGES-":
                    self._model.set_enabled_edges([])
                    self._view.update(self._model.snapshot())

                elif event == "-NEXT-":
                    if self._view.get_mode() == 'auto':
                        self._model.next_time_auto()
                        self._view.update(self._model.snapshot())
                    else:
                        selected_edges = self._view.get_selected_edges(values)
                        self._model.set_enabled_edges(selected_edges)
                        self._model.next_time()
                        self._view.update(self._model.snapshot())

                elif event == '-FIND_CONSENSUS-':
                    tao = self._view.get_tao(values)
                    self._model.set_tao(tao)
                    self._view.activate_automatic_mode()
                    self._model.find_consensus()

            except Exception as exc:
                self._view.show_error(str(exc))

        self._view.close()

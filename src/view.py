from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class GraphView:
    """PySimpleGUI view: renders a stable graph canvas and reads user selections."""

    CANVAS_WIDTH = 620
    CANVAS_HEIGHT = 520
    FIG_DPI = 100

    def __init__(self) -> None:
        self._mode = 'default'
        self._edge_label_to_pair: dict[str, tuple[int, int]] = {}
        self._position_cache: dict[int, tuple[float, float]] = {}
        self._last_node_order: tuple[int, ...] = tuple()

        controls = [
            [sg.Text("Time: 0", key="-TIME-", font=("Arial", 13, "bold"))],
            [sg.Text("Backend: not computed yet", key="-BACKEND-")],
            [sg.Text("Select the edges that participate in the next update:")],
            [
                sg.Listbox(
                    values=[],
                    select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                    size=(34, 11),
                    key="-ENABLED_EDGES-",
                    enable_events=False,
                )
            ],
            [sg.Button("Select all", key="-SELECT_ALL-"), sg.Button("Clear", key="-CLEAR_EDGES-")],
            [sg.Multiline("", key="-OPINIONS-", size=(34, 9), disabled=True)],
            [sg.Text("", key="-ERROR-", size=(36, 2), text_color="red")],
            [sg.Button("Next", key="-NEXT-", bind_return_key=True), sg.Exit()],
            [sg.Input(key="-TAO-"), sg.Button("Find Consesus", key="-FIND_CONSENSUS-", bind_return_key=True)]
        ]

        graph_frame = sg.Frame(
            "Network",
            [[sg.Canvas(size=(self.CANVAS_WIDTH, self.CANVAS_HEIGHT), key="-CANVAS-")]],
            pad=(0, 0),
        )

        layout = [
            [sg.Text("Hybrid DeGroot Opinion Network", font=("Arial", 16, "bold"))],
            [
                graph_frame,
                sg.VerticalSeparator(),
                sg.Column(controls, vertical_alignment="top", expand_x=False, expand_y=False),
            ],
        ]

        # resizable=False avoids Tk asking the layout to recompute its requested
        # size after each redraw. The Matplotlib widget below is also reused, so
        # the window keeps the same dimensions when Next is pressed.
        self._window = sg.Window(
            "Hybrid DeGroot MVC",
            layout,
            finalize=True,
            element_justification="center",
            resizable=False,
        )

        self._figure = plt.Figure(
            figsize=(self.CANVAS_WIDTH / self.FIG_DPI, self.CANVAS_HEIGHT / self.FIG_DPI),
            dpi=self.FIG_DPI,
        )
        self._figure_canvas_agg = FigureCanvasTkAgg(self._figure, self._window["-CANVAS-"].TKCanvas)
        self._figure_canvas_agg.get_tk_widget().configure(
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
        )
        self._figure_canvas_agg.get_tk_widget().pack(side="top", fill="none", expand=False)

    def get_tao(self, values: dict):
        return float(values.get('-TAO-'))

    def get_mode(self):
        return self._mode

    def activate_automatic_mode(self):
        self._mode = 'auto'
        self._window['-SELECT_ALL-'].update(disabled=True)
        self._window['-ENABLED_EDGES-'].update(disabled=True)
        self._window['-CLEAR_EDGES-'].update(disabled=True)

    def read_event(self):
        return self._window.read()

    def close(self) -> None:
        plt.close(self._figure)
        self._window.close()

    def show_error(self, message: str) -> None:
        self._window["-ERROR-"].update(message)

    def get_selected_edges(self, values: dict) -> list[tuple[int, int]]:
        selected_labels = values.get("-ENABLED_EDGES-", [])
        return [self._edge_label_to_pair[label] for label in selected_labels]

    def update(self, snapshot: dict) -> None:
        self._window["-ERROR-"].update("")
        self._window["-TIME-"].update(f"Time: {snapshot['time']}")
        self._window["-BACKEND-"].update(f"Backend: {snapshot['backend']}")
        self._update_edge_list(snapshot["edges"], snapshot["enabled_edges"])
        self._window["-OPINIONS-"].update(self._format_opinions(snapshot["opinions"]))
        self._window["-TAO-"].update(snapshot["tao"])
        self._draw_snapshot(snapshot)

    def _update_edge_list(
        self,
        edges: list[tuple[int, int, float]],
        enabled_edges: list[tuple[int, int]],
    ) -> None:
        enabled_set = set(enabled_edges)
        labels: list[str] = []
        selected_indices: list[int] = []
        self._edge_label_to_pair = {}

        for index, (u, v, influence) in enumerate(edges):
            label = f"{u} -> {v}   I={influence:.3f}"
            labels.append(label)
            self._edge_label_to_pair[label] = (u, v)
            if (u, v) in enabled_set:
                selected_indices.append(index)

        self._window["-ENABLED_EDGES-"].update(values=labels, set_to_index=selected_indices)

    @staticmethod
    def _format_opinions(opinions: dict[int, float]) -> str:
        lines = ["Opinions x_i(t):"]
        for node_id, opinion in sorted(opinions.items()):
            lines.append(f"  node {node_id}: {opinion:.6f}")
        return "\n".join(lines)

    def _draw_snapshot(self, snapshot: dict) -> None:
        """Redraw using the same Matplotlib/Tk widget.

        This is the key point: pressing Next must not create or pack a new
        FigureCanvasTkAgg. We clear the existing figure, draw again, and call
        draw_idle(). That prevents the canvas from growing and prevents the
        PySimpleGUI layout from shifting.
        """
        graph = nx.DiGraph()
        opinions: dict[int, float] = snapshot["opinions"]
        edges: list[tuple[int, int, float]] = snapshot["edges"]
        enabled_edges = set(snapshot["enabled_edges"])

        for node_id in snapshot["nodes"]:
            graph.add_node(node_id)
        graph.add_weighted_edges_from(edges)

        self._refresh_positions(snapshot["nodes"])
        pos = {node: self._position_cache[node] for node in graph.nodes}

        self._figure.clear()

        # Fixed axes positions keep the drawing area stable even when labels,
        # opinions, or edge selections change.
        ax = self._figure.add_axes([0.04, 0.08, 0.80, 0.84])
        cax = self._figure.add_axes([0.89, 0.18, 0.035, 0.64])

        if len(graph) > 0:
            node_values = [opinions[node] for node in graph.nodes]
            nx.draw_networkx_nodes(
                graph,
                pos,
                node_size=950,
                node_color=node_values,
                cmap=plt.cm.viridis,
                vmin=0,
                vmax=1,
                ax=ax,
            )

            labels = {node: f"{node}\n{opinions[node]:.2f}" for node in graph.nodes}
            nx.draw_networkx_labels(
                graph,
                pos,
                labels=labels,
                font_size=10,
                font_family="sans-serif",
                ax=ax,
            )

            active_edges = [(u, v) for u, v, _ in edges if (u, v) in enabled_edges]
            inactive_edges = [(u, v) for u, v, _ in edges if (u, v) not in enabled_edges]
            connectionstyle = "arc3,rad=0.12"

            nx.draw_networkx_edges(
                graph,
                pos,
                edgelist=inactive_edges,
                width=1.0,
                alpha=0.20,
                arrows=True,
                connectionstyle=connectionstyle,
                ax=ax,
            )
            nx.draw_networkx_edges(
                graph,
                pos,
                edgelist=active_edges,
                width=2.4,
                alpha=0.90,
                arrows=True,
                connectionstyle=connectionstyle,
                ax=ax,
            )

            edge_labels = {(u, v): f"{weight:.2f}" for u, v, weight in edges}
            nx.draw_networkx_edge_labels(
                graph,
                pos,
                edge_labels=edge_labels,
                font_size=9,
                connectionstyle=connectionstyle,
                ax=ax,
            )

        sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        self._figure.colorbar(sm, cax=cax, label="opinion")

        ax.set_title("Selected edges are darker/thicker")
        ax.set_xlim(-1.35, 1.35)
        ax.set_ylim(-1.35, 1.35)
        ax.set_aspect("equal", adjustable="box")
        ax.axis("off")

        self._figure_canvas_agg.draw_idle()

    def _refresh_positions(self, nodes: list[int]) -> None:
        node_order = tuple(sorted(nodes))
        if node_order == self._last_node_order:
            return

        graph = nx.DiGraph()
        graph.add_nodes_from(node_order)
        raw_pos = nx.circular_layout(graph) if node_order else {}
        self._position_cache = {node: (float(raw_pos[node][0]), float(raw_pos[node][1])) for node in node_order}
        self._last_node_order = node_order

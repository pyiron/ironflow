# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
For richer representations of node data allowing deeper analysis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ipywidgets as widgets
from IPython.display import display

if TYPE_CHECKING:
    from ironflow.gui.workflows.canvas_widgets import NodeWidget


class NodePresenter:
    """Handles the display of nodes with a representation."""

    def __init__(self):
        super().__init__()
        self.node_widget = None
        self._widgets = []
        self._toggles = []

        self._toggle_box = widgets.HBox([], layout={"flex_flow": "row wrap"})
        self._representation_box = widgets.VBox([], layout={"max_height": "325px"})

        self._border = "1px solid black"
        self.box = widgets.VBox(
            [self._toggle_box, self._representation_box],
            layout={"width": "100%", "border": ""}
        )

    def draw_for_node_widget(self, node_widget: NodeWidget):
        self.clear()
        self.node_widget = node_widget
        if node_widget is not None:
            self.draw()

    @staticmethod
    def _build_widgets(representations: dict) -> list[widgets.Output]:
        return [
            widgets.Output(layout={"border": "solid 1px gray"}) for _ in representations
        ]

    def _build_toggles(self, representations: dict) -> list[widgets.Checkbox]:
        toggles = []
        for i, label in enumerate(representations.keys()):
            toggle = widgets.Checkbox(
                description=label, value=i == 0, indent=False, layout={"width": "100px"}
            )
            toggle.observe(self._on_toggle)
            toggles.append(toggle)
        return toggles

    def _on_toggle(self, change: dict) -> None:
        if change["name"] == "value":
            self.draw()

    def clear(self):
        if self.node_widget is not None:
            self.node_widget.represent_button.pressed = False
            self.node_widget.represent_button.draw()  # Re-draw it as un-pressed
        self.node_widget = None

        for w in self._widgets:
            w.clear_output()
            self._close_widget(w)
        self._widgets = []
        self._toggles = []

        self.box.layout.border = ""
        self._toggle_box.children = []
        self._representation_box.children = []

    def update(self) -> None:
        if (
                self.node_widget is not None and
                self.node_widget.node.representation_updated
        ):
            self.draw()

    def draw(self):
        representations_dict = self.node_widget.node.representations

        if len(representations_dict) != len(self._widgets):
            self._widgets = self._build_widgets(representations_dict)
            self._toggles = self._build_toggles(representations_dict)

        for (toggle, widget, representation) in zip(
            self._toggles, self._widgets, representations_dict.values()
        ):
            widget.clear_output()
            widget.layout.border = ""
            if toggle.value:
                widget.layout.border = self._border
                with widget:
                    display(representation)

        self._toggle_box.children = self._toggles
        self._representation_box.children = self._widgets

        self.node_widget.node.representation_updated = False

    def close(self) -> None:
        self.draw_for_node_widget(None)

    def _close_widget(self, w):
        if hasattr(w, "children"):
            for c in w.children:
                self._close_widget(c)
        w.layout.close()
        try:
            w.style.close()
        except AttributeError:
            pass
        w.close()

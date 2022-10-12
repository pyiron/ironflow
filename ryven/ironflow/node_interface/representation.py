# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

from ryven.ironflow.node_interface.base import NodeInterfaceBase
from IPython.display import display
import ipywidgets as widgets

from typing import TYPE_CHECKING, Optional, Callable
if TYPE_CHECKING:
    from ryven.ironflow.gui import GUI
    from ryven.ironflow.canvas_widgets.nodes import RepresentableNodeWidget

__author__ = "Liam huber"
__copyright__ = (
    "Copyright 2022, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "Sept 20, 2022"


class NodePresenter(NodeInterfaceBase):
    """Handles the display of nodes with a representation."""

    def __init__(self, gui: GUI, layout: Optional[dict] = None):
        super().__init__(gui=gui, layout=layout)
        self._node_widget = None
        self._widgets = []
        self._toggles = []

    @property
    def node_widget(self) -> RepresentableNodeWidget | None:
        return self._node_widget

    @node_widget.setter
    def node_widget(self, new_node_widget: RepresentableNodeWidget | None):
        if self._node_widget is not None:
            self.clear_output()
            self._node_widget.represent_button.pressed = False

        if new_node_widget is not None:
            new_node_widget.node.representation_updated = True
            self._node_widget = new_node_widget
            self._widgets = self._build_widgets(new_node_widget.node.representations)
            self._toggles = self._build_toggles(new_node_widget.node.representations)
        else:
            self._node_widget = None
            self._widgets = []
            self._toggles = []

    @staticmethod
    def _build_widgets(representations: dict) -> list[widgets.Output]:
        return [widgets.Output(layout={"border": "solid 1px gray"}) for _ in representations]

    def _build_toggles(self, representations: dict) -> list[widgets.Checkbox]:
        toggles = []
        for i, label in enumerate(representations.keys()):
            toggle = widgets.Checkbox(description=label, value=i == 0, indent=False, layout={"width": "100px"})
            toggle.observe(self._on_toggle)
            toggles.append(toggle)
        return toggles

    def _on_toggle(self, change: dict) -> None:
        if change['name'] == 'value':
            self._draw()

    def _draw(self):
        self.clear_output()

        representations = []
        for (toggle, widget, representation) in zip(
                self._toggles,
                self._widgets,
                self.node_widget.node.representations.values()
        ):
            if toggle.value:
                with widget:
                    display(representation)
                representations.append(widget)

        with self.output:
            display(
                widgets.VBox([
                    widgets.HBox(self._toggles, layout={"flex_flow": "row wrap"}),
                    *representations
                ])
            )

    def draw(self):
        if self.node_widget is not None and self.node_widget.node.representation_updated:
            self._draw()
            self.node_widget.node.representation_updated = False

    def clear_output(self):
        for w in self._widgets:
            w.clear_output()
        super().clear_output()

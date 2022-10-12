# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

from ryven.ironflow.node_interface_abc import NodeInterfaceBase
from IPython.display import display

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from ironflow.ryven.ironflow.gui import GUI
    from ironflow.ryven.ironflow.canvas_widgets import RepresentableNodeWidget

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

    def draw(self):
        if self.node_widget is not None and self.node_widget.node.representation_updated:
            self.clear_output()
            with self.output:
                for rep in self.node_widget.node.representations:
                    display(rep)
            self.node_widget.node.representation_updated = False

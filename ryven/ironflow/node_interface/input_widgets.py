# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.


from __future__ import annotations

import ipywidgets as widgets

from ryven.NENV import Node
from ryven.ironflow import GUI

__author__ = "Joerg Neugebauer, Liam Huber"
__copyright__ = (
    "Copyright 2022, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "Sept 21, 2022"


class SliderControl:
    def __init__(self, gui: GUI, node: Node):
        self.gui = gui
        self.node = node
        self.widget = widgets.FloatSlider(
            value=self.node.val, min=0, max=10, continuous_update=False
        )

        self.widget.observe(self.widget_change, names="value")

    def widget_change(self, change: dict) -> None:
        self.node.set_state({"val": change["new"]}, 0)
        self.node.update_event()
        self.gui.flow_canvas.redraw()

# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Specialty widgets for directly controlling node input.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ipywidgets as widgets

if TYPE_CHECKING:
    from ironflow.model.node import Node
    from ironflow.gui.workflows.screen import WorkflowsGUI


class SliderControl:
    def __init__(self, screen: WorkflowsGUI, node: Node):
        self.screen = screen
        self.node = node
        self.widget = widgets.FloatSlider(
            value=self.node.val, min=0, max=10, continuous_update=False
        )

        self.widget.observe(self.widget_change, names="value")

    def widget_change(self, change: dict) -> None:
        self.node.set_state({"val": change["new"]}, 0)
        self.node.update_event()
        self.screen.redraw_active_flow_canvas()

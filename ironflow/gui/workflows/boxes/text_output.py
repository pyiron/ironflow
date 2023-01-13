# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
For giving text feedback to the user.
"""

from __future__ import annotations

import ipywidgets as widgets
from IPython.display import display

from ironflow.gui.draws_widgets import DrawsWidgets


class TextOut(DrawsWidgets):
    main_widget_class = widgets.VBox

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.width = "100%"
        self.widget.border = "1px solid black"
        self._output = widgets.Output()
        self._button = widgets.Button(
            tooltip="Clear output",
            description="clear",
            layout={"width": "100px"},
        )
        self._button.on_click(self._click_button)

    def clear(self):
        self._output.clear_output()
        self.widget.children = []
        super().clear()

    def _click_button(self, change: dict) -> None:
        self.clear()

    def print(self, msg: str):
        self._output.clear_output()
        with self._output:
            display(msg)
        self.widget.children = [self._output, self._button]

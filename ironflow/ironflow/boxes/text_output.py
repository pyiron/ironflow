# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.


from __future__ import annotations

import ipywidgets as widgets
from IPython.display import display
from ironflow.ironflow.boxes.base import Box

__author__ = "Liam Huber"
__copyright__ = (
    "Copyright 2022, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "Oct 7, 2022"


class TextOut(Box):
    box_class = widgets.VBox

    def __init__(self):
        super().__init__()
        self._output = widgets.Output()
        self._button = widgets.Button(
            tooltip="Clear output",
            description="clear",
            layout={"width": "100px"},
        )
        self._button.on_click(self._click_button)

    @property
    def layout(self):
        return widgets.Layout(
            width="100%",
            border="1px solid black",
        )

    def clear(self):
        super().clear()
        self._output.clear_output()

    def _click_button(self, change: dict) -> None:
        self.clear()

    def print(self, msg: str):
        self._output.clear_output()
        with self._output:
            display(msg)
        self.box.children = [self._output, self._button]

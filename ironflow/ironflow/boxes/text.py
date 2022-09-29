# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.


from __future__ import annotations

import ipywidgets as widgets
from IPython.display import display
from ironflow.ironflow.boxes.base import Box


class TextOut:
    def __init__(self):
        self._output = widgets.Output()
        self._button = widgets.Button(
            tooltip="Clear output",
            description="clear",
            layout={"width": "100px", "visibility": "hidden"},
        )
        self._button.on_click(self._click_button)

    def clear(self):
        self._output.clear_output()
        self._hide_button()

    def _click_button(self, change: dict) -> None:
        self.clear()

    def _hide_button(self):
        self._button.layout.visibility = "hidden"
        self._button.layout.height = "0px"

    def _show_button(self):
        self._button.layout.visibility = "visible"
        self._button.layout.height = "auto"

    @property
    def box(self) -> widgets.VBox:
        layout = widgets.Layout(
            width="100%",
            border="1px solid black",
        )
        return widgets.VBox([self._output, self._button], layout=layout)

    def print(self, msg: str):
        self._output.clear_output()
        with self._output:
            display(msg)
        self._show_button()

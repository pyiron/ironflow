# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.


from __future__ import annotations

import ipywidgets as widgets
from IPython.display import display


class TextOut:
    def __init__(self):
        layout = widgets.Layout(
            width="100%",
            border="1px solid black",
        )
        self._box = widgets.VBox([], layout=layout)
        self._output = widgets.Output()
        self._button = widgets.Button(
            tooltip="Clear output",
            description="clear",
            layout={"width": "100px"},
        )
        self._button.on_click(self._click_button)

    def clear(self):
        self._output.clear_output()
        self._box.children = []

    def _click_button(self, change: dict) -> None:
        self.clear()

    @property
    def box(self) -> widgets.VBox:
        return self._box

    def print(self, msg: str):
        self._output.clear_output()
        with self._output:
            display(msg)
        self._box.children = [self._output, self._button]

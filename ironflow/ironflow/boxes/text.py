# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.


from __future__ import annotations

import ipywidgets as widgets
from IPython.display import display
from ironflow.ironflow.boxes.base import Box
from typing import Callable, Optional, Any


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


class TextIn(Box):
    def __init__(self):
        self._box = widgets.HBox([])

        self.input_field = widgets.Text(value="INIT VALUE", description="DESCRIPTION")
        layout = widgets.Layout(width="50px")
        self.ok_button = widgets.Button(tooltip="Confirm", icon="check", layout=layout)
        self._last_ok_callback = None
        self.cancel_button = widgets.Button(tooltip="Cancel", icon="ban", layout=layout)
        # TODO: Use xmark once this is available
        self.cancel_button.on_click(self.close)

    @property
    def box(self):
        return self._box

    def clear(self):
        self._box.children = []
        self._clear_callback()

    @property
    def value(self):
        return self.input_field.value

    def wrap_callback(self, callback: callable) -> callable:
        def wrapped_callback(change: dict) -> None:
            callback(change)
            self.clear()

        return wrapped_callback

    def _clear_callback(self):
        if self._last_ok_callback is not None:
            self.input_field.on_submit(self._last_ok_callback, remove=True)
            self.ok_button.on_click(self._last_ok_callback, remove=True)

    def _set_callback(self, callback: callable):
        wrapped_callback = self.wrap_callback(callback)
        self.input_field.on_submit(wrapped_callback)
        self.ok_button.on_click(wrapped_callback)
        self._last_ok_callback = wrapped_callback

    def open(
            self,
            description: str,
            callback: Callable,
            initial_value: Any,
            description_tooltip: Optional[str] = None,
            ok_tooltip: str = "Confirm",
            cancel_tooltip: str = "Cancel"
    ):
        self._box.children = [
            self.input_field,
            self.ok_button,
            self.cancel_button
        ]
        self.input_field.description = description
        description_tooltip = description_tooltip if description_tooltip is not None else description
        self.input_field.description_tooltip = description_tooltip
        self.input_field.value = initial_value
        self.ok_button.tooltip = ok_tooltip
        self.cancel_button.tooltip = cancel_tooltip

        self._set_callback(callback)

    def close(self, change: None):
        self.clear()

from __future__ import annotations

from typing import Callable, Any, Optional

import ipywidgets as widgets

from ironflow.ironflow.boxes.base import Box


class UserInput(Box):
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
